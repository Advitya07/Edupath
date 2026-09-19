"""Resilient LLM gateway: rotates Gemini keys on 429 and falls back to Ollama."""
from __future__ import annotations
from itertools import cycle
from app.config.settings import get_settings


class KeyRotator:
    def __init__(self, keys: list[str]):
        self.keys = keys
        self._cycle = cycle(keys) if keys else None

    def next_key(self) -> str | None:
        return next(self._cycle) if self._cycle else None


class LLMGateway:
    def __init__(self):
        self.settings = get_settings()
        self.rotator = KeyRotator(self.settings.gemini_keys)

    def _ollama(self):
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(model="llama3.2", base_url=self.settings.ollama_base_url, temperature=0.2)

    async def invoke(self, prompt: str) -> str:
        """Prefer Gemini unless configured otherwise; 429 moves to the next key."""
        if not self.settings.use_ollama and self.rotator.keys:
            tried = set()
            while len(tried) < len(self.rotator.keys):
                key = self.rotator.next_key()
                tried.add(key)
                try:
                    from langchain_google_genai import ChatGoogleGenerativeAI
                    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=key, temperature=0.2)
                    return (await model.ainvoke(prompt)).content
                except Exception as exc:
                    # Continue for 429 quota errors and transient provider failures alike.
                    if "429" not in str(exc) and len(tried) >= len(self.rotator.keys):
                        break
        try:
            return (await self._ollama().ainvoke(prompt)).content
        except Exception as exc:
            raise RuntimeError("No configured LLM provider is available") from exc


llm = LLMGateway()
