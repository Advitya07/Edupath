"""Compatibility wrapper for the existing assessment router."""
from app.ai.service import ai_service


async def generate_quiz(
    career: str,
    skills: list[str],
    topic: str | None = None,
    *,
    profile: dict | None = None,
    skill_state: dict | None = None,
    recent_quiz: dict | None = None,
    previous_topics: list[str] | None = None,
) -> list[dict]:
    learner_profile = profile or {
        "career_target": career,
        "skills": skills,
        "skill_profile": [{"name": skill, "level": 5} for skill in skills],
    }

    if topic:
        return await ai_service.generate_topic_quiz(
            profile=learner_profile,
            career_goal=career,
            selected_topic=topic,
            previous_topics=previous_topics or [],
            skill_scores=(skill_state or {}).get("scores") if skill_state else None,
        )

    if skill_state and skill_state.get("scores"):
        weak_topics = [t for t, s in sorted(skill_state["scores"].items(), key=lambda x: x[1]) if s < 55]
        if not weak_topics and skill_state["scores"]:
            sorted_by_score = sorted(skill_state["scores"].items(), key=lambda x: x[1])
            weak_topics = [t for t, _ in sorted_by_score[:2]]
        return await ai_service.generate_reassessment_quiz(
            learner_profile,
            skill_state["scores"],
            recent_quiz or {},
            weak_topics,
            None,
        )
    return await ai_service.generate_initial_quiz(learner_profile, career)
