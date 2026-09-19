from uuid import uuid4
from fastapi import APIRouter
from app.schemas.chat import ChatRequest
from app.ai.chains.mentor_chain import mentor_reply
from app.database.mongodb import db

router = APIRouter(prefix="/chat", tags=["mentor"])


@router.post("")
async def chat(payload: ChatRequest):
    reply = await mentor_reply(payload.message, payload.current_topic, payload.career_target, payload.weak_gaps)
    await db.insert("chat_history", {"id": str(uuid4()), **payload.model_dump(), "reply": reply})
    return {"reply": reply}
