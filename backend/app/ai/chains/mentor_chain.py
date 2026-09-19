from app.ai.llm import AIServiceError
from app.ai.service import ai_service


async def mentor_reply(message: str, topic: str, career: str, gaps: list[str]) -> str:
    try:
        return await ai_service.generate_chat_response(
            {"career": career, "current_focus": topic, "weak_skills": gaps}, message, []
        )
    except AIServiceError:
        pass
    focus = gaps[0] if gaps else topic
    return f"Great question. For {focus}, start by naming the input, expected output, and one edge case. Then build a tiny 20-minute example. What part of {message[:80]} feels least clear?"
