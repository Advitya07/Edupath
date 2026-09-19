from app.ai.llm import llm
from app.config.settings import get_settings


async def mentor_reply(message: str, topic: str, career: str, gaps: list[str]) -> str:
    settings = get_settings()
    if settings.gemini_keys or settings.use_ollama:
        try:
            prompt = f"You are a concise, encouraging mentor for a {career}. Current topic: {topic}; weak gaps: {', '.join(gaps) or 'none'}. Answer: {message}"
            return await llm.invoke(prompt)
        except Exception:
            pass
    focus = gaps[0] if gaps else topic
    return f"Great question. For {focus}, start by naming the input, expected output, and one edge case. Then build a tiny 20-minute example. What part of {message[:80]} feels least clear?"
