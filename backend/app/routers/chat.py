from uuid import uuid4
from fastapi import APIRouter
from datetime import datetime, timezone
from app.schemas.chat import ChatRequest
from app.ai.llm import AIServiceError
from app.ai.service import ai_service
from app.database.mongodb import db

router = APIRouter(prefix="/chat", tags=["mentor"])


@router.post("")
async def chat(payload: ChatRequest):
    profile = await db.find_one("profiles", {"user_id": payload.user_id}) if payload.user_id else None
    state = await db.find_one("skill_states", {"user_id": payload.user_id}) if payload.user_id else None
    roadmap = await db.find_one("roadmaps", {"user_id": payload.user_id}) if payload.user_id else None
    recommendation = await db.find_one("recommendations", {"user_id": payload.user_id}) if payload.user_id else None
    progress = await db.find_all("progress") if payload.user_id else []
    recent_quiz = next((item for item in reversed(progress) if item.get("user_id") == payload.user_id), {})
    history = await db.find_all("chat_history")
    user_chat = [item for item in history if item.get("user_id") == payload.user_id][-3:]
    recent_history = []
    for item in user_chat:
        if item.get("message"):
            recent_history.append({"role": "user", "content": item["message"]})
        if item.get("reply"):
            recent_history.append({"role": "assistant", "content": item["reply"]})
    nodes = (roadmap or {}).get("nodes", [])
    focus_node = next((node for node in nodes if node.get("priority") == "high"), None) or next(
        (node for node in nodes if node.get("status") == "in_progress"), None
    )
    scores = (state or {}).get("scores", {})
    context = {
        "career": (profile or {}).get("career_target", payload.career_target),
        "current_focus": (focus_node or {}).get("topic", payload.current_topic),
        "skill_scores": scores,
        "weak_skills": [topic for topic, score in scores.items() if score < 55] or payload.weak_gaps,
        "current_roadmap_node": (focus_node or {}).get("topic", payload.current_topic),
        "latest_recommendations": (recommendation or {}).get("recommendations", {}).get("next_focus", []),
        "latest_quiz_performance": {
            "overall": recent_quiz.get("overall"),
            "current_topic_scores": recent_quiz.get("current_topic_scores", {}),
        } if recent_quiz else None,
    }
    try:
        reply = await ai_service.generate_chat_response(context, payload.message, recent_history)
        ai_status = {"success": True}
    except AIServiceError as exc:
        reply = "AI service is temporarily unavailable. Your saved roadmap and curated resources are still available."
        ai_status = exc.as_dict()
    await db.insert("chat_history", {
        "id": str(uuid4()),
        "user_id": payload.user_id,
        "role": "user",
        "message": payload.message,
        "reply": reply,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"reply": reply, "ai": ai_status}
