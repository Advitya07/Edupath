"""Single-provider Ollama gateway with safe, validated structured responses."""
from __future__ import annotations
import asyncio
import json
import logging
import re
from typing import TypeVar
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, ValidationError

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
SchemaT = TypeVar("SchemaT", bound=BaseModel)


class AIServiceError(RuntimeError):
    """A client-safe AI failure. The details stay in server logs."""

    def __init__(self, code: str, message: str = "AI service is temporarily unavailable.") -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def as_dict(self) -> dict[str, str | bool]:
        return {"success": False, "error": self.code, "message": self.message}


class OllamaProvider:
    """The only active model provider. Frontend code never talks to Ollama."""

    def __init__(self):
        self.settings = get_settings()
        self._active_base_url: str | None = None

    def _request_sync(self, payload: dict) -> dict:
        candidates = []
        if self._active_base_url:
            candidates.append(self._active_base_url)
        default_url = self.settings.ollama_base_url.rstrip("/")
        if default_url not in candidates:
            candidates.append(default_url)
        if "11434" in self.settings.ollama_base_url:
            alt = self.settings.ollama_base_url.replace("11434", "11435").rstrip("/")
            if alt not in candidates:
                candidates.append(alt)

        last_error = None
        for base in candidates:
            endpoint = f"{base}/api/chat"
            request = Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urlopen(request, timeout=self.settings.ollama_timeout_seconds) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    self._active_base_url = base
                    return data
            except HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                logger.warning("Ollama request to %s failed with HTTP %s: %s", base, exc.code, body[:500])
                if self._active_base_url == base:
                    self._active_base_url = None
                if exc.code == 404:
                    last_error = AIServiceError("OLLAMA_MODEL_NOT_FOUND")
                    continue
                raise AIServiceError("AI_SERVICE_UNAVAILABLE") from exc
            except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
                logger.warning("Ollama request to %s failed: %s", base, exc)
                if self._active_base_url == base:
                    self._active_base_url = None
                last_error = AIServiceError("AI_SERVICE_UNAVAILABLE")
                continue

        if last_error:
            raise last_error
        raise AIServiceError("AI_SERVICE_UNAVAILABLE")

    async def invoke(self, prompt: str, *, json_mode: bool = False) -> str:
        payload = {
            "model": self.settings.ollama_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.2},
        }
        if json_mode:
            payload["format"] = "json"
        try:
            response = await asyncio.to_thread(self._request_sync, payload)
            content = response.get("message", {}).get("content")
            if not isinstance(content, str) or not content.strip():
                raise ValueError("Ollama returned an empty response")
            return content.strip()
        except AIServiceError:
            raise
        except Exception as exc:
            logger.exception("Unexpected Ollama response failure")
            raise AIServiceError("AI_SERVICE_UNAVAILABLE") from exc

    @staticmethod
    def _decode_json(raw: str) -> object:
        text = raw.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        if "```" in text:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
            if match:
                candidate = match.group(1).strip()
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    text = candidate
        starts = [position for position in (text.find("{"), text.find("[")) if position >= 0]
        if not starts:
            raise json.JSONDecodeError("No JSON structure found", text, 0)
        start = min(starts)
        end = max(text.rfind("}"), text.rfind("]"))
        if end <= start:
            raise json.JSONDecodeError("Invalid JSON boundary", text, 0)
        return json.loads(text[start : end + 1])

    async def invoke_structured(self, prompt: str, schema: type[SchemaT]) -> SchemaT:
        """Use Ollama JSON mode, then permit exactly one bounded repair attempt."""
        raw = ""
        repair_prompt = prompt
        for attempt in range(2):
            try:
                raw = await self.invoke(repair_prompt, json_mode=True)
                return schema.model_validate(self._decode_json(raw))
            except AIServiceError:
                raise
            except (ValidationError, ValueError, json.JSONDecodeError, TypeError) as exc:
                logger.warning("Invalid structured Ollama output on attempt %s: %s", attempt + 1, exc)
                if attempt:
                    break
                repair_prompt = (
                    f"{prompt}\n\nYour previous response was invalid. Return only one JSON value matching "
                    f"this schema exactly: {json.dumps(schema.model_json_schema())}. "
                    f"Do not include markdown. Previous response: {raw[:6000]}"
                )
        raise AIServiceError("AI_RESPONSE_INVALID", "AI returned an invalid structured response. Please try again.")


llm = OllamaProvider()
