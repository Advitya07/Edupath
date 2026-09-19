import json
from uuid import uuid4
from app.ai.llm import llm
from app.config.settings import get_settings

QUESTION_BANK = [
    ("JavaScript", "What does Array.prototype.map return?", ["The original array", "A new transformed array", "A boolean", "Nothing"], 1),
    ("React", "Which hook stores component state?", ["useMemo", "useEffect", "useState", "useRef"], 2),
    ("APIs", "Which HTTP method is conventionally idempotent for replacing a resource?", ["POST", "PUT", "PATCH", "CONNECT"], 1),
    ("SQL", "Which clause filters aggregated query results?", ["WHERE", "ORDER BY", "HAVING", "GROUP BY"], 2),
    ("Python", "What does a Python generator use to emit a lazy sequence?", ["return", "yield", "await", "pass"], 1),
    ("Docker", "What is the primary role of a Docker image?", ["Runtime process", "Immutable app template", "Database", "Network"], 1),
    ("Git", "Which command integrates another branch's history?", ["git clone", "git merge", "git status", "git init"], 1),
    ("System Design", "Which property means a system keeps operating despite node failure?", ["Latency", "Fault tolerance", "Throughput", "Coupling"], 1),
    ("Testing", "What is a unit test intended to isolate?", ["A deployed cluster", "One small behavior", "User research", "Production data"], 1),
    ("Security", "Where should a web app generally store a password?", ["Plaintext database", "Client-side state", "Salted password hash", "URL parameter"], 2),
]


def fallback_questions(topic: str | None = None) -> list[dict]:
    rows = [r for r in QUESTION_BANK if not topic or r[0].lower() == topic.lower()]
    rows = rows or QUESTION_BANK
    return [{"id": str(uuid4()), "topic": t, "prompt": p, "options": o, "answer_index": a} for t, p, o, a in rows[:10]]


async def generate_quiz(career: str, skills: list[str], topic: str | None = None) -> list[dict]:
    settings = get_settings()
    if not (settings.gemini_keys or settings.use_ollama):
        return fallback_questions(topic)
    prompt = f'''Create exactly 10 four-option MCQs for a {career} diagnostic. Resume skills: {skills}. Topic: {topic or "core skills"}. Return only JSON array objects with topic, prompt, options, answer_index.'''
    try:
        raw = await llm.invoke(prompt)
        data = json.loads(raw[raw.find("["):raw.rfind("]") + 1])
        if not isinstance(data, list) or not data:
            raise ValueError("empty quiz")
        return [{"id": str(uuid4()), **q} for q in data[:10]]
    except Exception:
        return fallback_questions(topic)
