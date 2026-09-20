import asyncio
from datetime import datetime, timezone
import logging
from uuid import uuid4
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.ai.llm import AIServiceError
from app.ai.service import ai_service
from app.database.mongodb import db
from app.schemas.quiz import QuizRequest, QuizSubmission
from app.ai.chains.quiz_chain import generate_quiz
from app.ai.chains.roadmap_chain import apply_recommendations, make_roadmap
from app.services.scoring_service import score_submission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assessment", tags=["assessment"])

# In-flight request tracking to prevent concurrent duplicate Ollama calls
_in_flight_generations: dict[tuple[str, str | None], asyncio.Task] = {}
_in_flight_submissions: dict[str, asyncio.Task] = {}


async def _perform_generate(payload: QuizRequest) -> dict | JSONResponse:
    profile = await db.find_one("profiles", {"user_id": payload.user_id}) if payload.user_id else None
    profile = profile or {
        "career_target": payload.career_target,
        "skills": payload.skills,
        "skill_profile": [{"name": skill, "level": 5} for skill in payload.skills],
    }
    skill_state = await db.find_one("skill_states", {"user_id": payload.user_id}) if payload.user_id else None
    reassessment = bool(payload.topic or (skill_state or {}).get("scores"))
    kind = "reassessment" if reassessment else "initial"
    profile_version = profile.get("profile_version", 0)

    progress = await db.find_all("progress") if payload.user_id else []
    recent = next((item for item in reversed(progress) if item.get("user_id") == payload.user_id), {})
    try:
        logger.info("[QUIZ] Generating questions via Ollama for career=%s topic=%s", payload.career_target, payload.topic)
        questions = await generate_quiz(
            payload.career_target,
            profile.get("skills", payload.skills),
            payload.topic,
            profile=profile,
            skill_state=skill_state if reassessment else None,
            recent_quiz={"topic_scores": recent.get("current_topic_scores", {})},
        )
    except AIServiceError as exc:
        return JSONResponse(status_code=503, content=exc.as_dict())

    quiz = {
        "id": str(uuid4()),
        "user_id": payload.user_id,
        "career_target": payload.career_target,
        "kind": kind,
        "profile_version": profile_version,
        "skill_state_version": (skill_state or {}).get("version", 0),
        "topic": payload.topic,
        "questions": questions,
        "submitted": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.insert("quizzes", quiz)
    logger.info("[QUIZ] Generated quiz %s with %d questions", quiz["id"], len(questions))
    return quiz


@router.post("/generate")
async def generate(payload: QuizRequest):
    if payload.user_id:
        gen_key = (payload.user_id, payload.topic)
        # 1. Deduplicate concurrent in-flight generation requests for same user and topic
        existing_task = _in_flight_generations.get(gen_key)
        if existing_task and not existing_task.done():
            logger.info("[QUIZ] Reusing in-flight quiz generation for user=%s topic=%s", payload.user_id, payload.topic)
            return await existing_task

        # 2. Check for active unsubmitted quiz for this user and topic
        all_quizzes = await db.find_all("quizzes")
        unsubmitted = [
            q for q in all_quizzes
            if q.get("user_id") == payload.user_id
            and q.get("topic") == payload.topic
            and not q.get("submitted")
        ]
        if unsubmitted:
            unsubmitted.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            logger.info("[QUIZ] Returning active unsubmitted quiz %s for user=%s topic=%s", unsubmitted[0].get("id"), payload.user_id, payload.topic)
            return unsubmitted[0]

        task = asyncio.create_task(_perform_generate(payload))
        _in_flight_generations[gen_key] = task
        try:
            return await task
        finally:
            _in_flight_generations.pop(gen_key, None)

    return await _perform_generate(payload)


async def _perform_submit(payload: QuizSubmission, quiz: dict) -> dict:
    user_id = payload.user_id or quiz.get("user_id")
    previous_state = await db.find_one("skill_states", {"user_id": user_id}) if user_id else None
    previous_scores = (previous_state or {}).get("scores") or payload.previous_scores
    result = score_submission(quiz["questions"], [a.model_dump() for a in payload.answers], previous_scores)
    now = datetime.now(timezone.utc).isoformat()
    result["user_id"] = user_id
    result["assessed_at"] = now

    if user_id:
        scores = {**previous_scores, **result["topic_scores"]}
        history = dict((previous_state or {}).get("history", {}))
        trends = {}
        for topic, current_score in result["current_topic_scores"].items():
            previous_score = previous_scores.get(topic)
            cumulative_score = result["topic_scores"][topic]
            history[topic] = [
                *history.get(topic, []),
                {"quiz_id": payload.quiz_id, "current": current_score, "cumulative": cumulative_score, "assessed_at": now},
            ][-20:]
            trends[topic] = round(cumulative_score - float(previous_score), 1) if previous_score is not None else 0
        state = {
            "user_id": user_id,
            "scores": scores,
            "history": history,
            "trends": trends,
            "last_assessed": now,
            "version": int((previous_state or {}).get("version", 0)) + 1,
        }
        await db.upsert("skill_states", {"user_id": user_id}, state)
        result["skill_scores"] = scores
        result["skill_state_version"] = state["version"]
    else:
        state = None
        result["skill_scores"] = result["topic_scores"]

    await db.insert("progress", {"id": str(uuid4()), "quiz_id": payload.quiz_id, **result})
    await db.upsert("quizzes", {"id": payload.quiz_id}, {**quiz, "submitted": True, "submitted_at": now})

    if user_id and state:
        profile = await db.find_one("profiles", {"user_id": user_id}) or {"career_target": quiz["career_target"]}
        roadmap = await db.find_one("roadmaps", {"user_id": user_id})
        if not roadmap:
            roadmap = make_roadmap(
                quiz.get("career_target") or profile.get("career_target", "Full Stack Engineer"),
                state["scores"],
                profile.get("skills", []),
            )
            roadmap["roadmap_version"] = 0
        history_summary = {
            topic: entries[-2:]
            for topic, entries in state["history"].items()
            if topic in result["current_topic_scores"]
        }
        try:
            logger.info("[QUIZ] Analyzing post-quiz performance via Ollama for quiz_id=%s", payload.quiz_id)
            recommendations = await ai_service.analyze_post_quiz_performance(
                profile,
                state["scores"],
                history_summary,
                {"quiz_id": payload.quiz_id, "topic_scores": result["current_topic_scores"], "trends": trends},
                roadmap,
            )
            recommendation_record = {
                "user_id": user_id,
                "skill_state_version": state["version"],
                "recommendations": recommendations,
                "updated_at": now,
            }
            await db.upsert("recommendations", {"user_id": user_id}, recommendation_record)
            result["recommendations"] = recommendations
            result["ai"] = {"success": True}
            updated_roadmap = apply_recommendations(roadmap, state["scores"], recommendations)
            updated_roadmap.update({
                "user_id": user_id,
                "skill_state_version": state["version"],
                "roadmap_version": int(roadmap.get("roadmap_version", 0)) + 1,
                "recommendations": recommendations,
                "updated_at": now,
            })
            await db.upsert("roadmaps", {"user_id": user_id}, updated_roadmap)
            result["roadmap"] = updated_roadmap
        except AIServiceError as exc:
            # Scores persist even when Ollama is unavailable. Existing roadmap data
            # is preserved and updated with latest scores without lost state.
            result["ai"] = exc.as_dict()
            updated_roadmap = apply_recommendations(roadmap, state["scores"], None)
            updated_roadmap.update({
                "user_id": user_id,
                "skill_state_version": state["version"],
                "roadmap_version": int(roadmap.get("roadmap_version", 0)) + 1,
                "updated_at": now,
            })
            await db.upsert("roadmaps", {"user_id": user_id}, updated_roadmap)
            result["roadmap"] = updated_roadmap
    return result


@router.post("/submit")
async def submit(payload: QuizSubmission):
    sub_key = payload.quiz_id
    existing_task = _in_flight_submissions.get(sub_key)
    if existing_task and not existing_task.done():
        logger.info("[QUIZ] Reusing in-flight submission task for quiz_id=%s", payload.quiz_id)
        return await existing_task

    quiz = await db.find_one("quizzes", {"id": payload.quiz_id})
    if not quiz:
        return {"overall": 0, "topic_scores": {}, "details": [], "error": "Quiz expired; generate a new quiz."}

    if quiz.get("submitted"):
        all_progress = await db.find_all("progress")
        existing_progress = next((p for p in reversed(all_progress) if p.get("quiz_id") == payload.quiz_id), None)
        if existing_progress:
            logger.info("[QUIZ] Quiz %s already submitted, returning existing progress", payload.quiz_id)
            return existing_progress

    task = asyncio.create_task(_perform_submit(payload, quiz))
    _in_flight_submissions[sub_key] = task
    try:
        return await task
    finally:
        _in_flight_submissions.pop(sub_key, None)
