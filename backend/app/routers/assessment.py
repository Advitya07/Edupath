from uuid import uuid4
from fastapi import APIRouter
from app.database.mongodb import db
from app.schemas.quiz import QuizRequest, QuizSubmission
from app.ai.chains.quiz_chain import generate_quiz
from app.services.scoring_service import score_submission

router = APIRouter(prefix="/assessment", tags=["assessment"])


@router.post("/generate")
async def generate(payload: QuizRequest):
    quiz = {"id": str(uuid4()), "career_target": payload.career_target, "questions": await generate_quiz(payload.career_target, payload.skills, payload.topic)}
    await db.insert("quizzes", quiz)
    return quiz


@router.post("/submit")
async def submit(payload: QuizSubmission):
    quiz = await db.find_one("quizzes", {"id": payload.quiz_id})
    if not quiz:
        return {"overall": 0, "topic_scores": {}, "details": [], "error": "Quiz expired; generate a new quiz."}
    result = score_submission(quiz["questions"], [a.model_dump() for a in payload.answers], payload.previous_scores)
    await db.insert("progress", {"id": str(uuid4()), "quiz_id": payload.quiz_id, **result})
    return result
