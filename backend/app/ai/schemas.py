"""Validated shapes accepted from the local model before persistence."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictAIModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class ProfileSkill(StrictAIModel):
    name: str = Field(min_length=1, max_length=100)
    level: int = Field(default=5, ge=1, le=10)
    evidence: list[str] = Field(default_factory=list, max_length=6)

    @field_validator("name", mode="before")
    @classmethod
    def coerce_name(cls, v):
        return str(v or "").strip() or "General Skill"

    @field_validator("level", mode="before")
    @classmethod
    def coerce_level(cls, v):
        try:
            val = int(float(v))
            return max(1, min(10, val))
        except (ValueError, TypeError):
            return 5

    @field_validator("evidence", mode="before")
    @classmethod
    def coerce_evidence(cls, v):
        if isinstance(v, str):
            return [v.strip()] if v.strip() else ["Demonstrated in profile"]
        if isinstance(v, list):
            res = [str(x).strip() for x in v if str(x).strip()]
            return res[:6] if res else ["Demonstrated in profile"]
        return ["Demonstrated in profile"]


class ResumeProject(StrictAIModel):
    name: str = Field(min_length=1, max_length=160)
    technologies: list[str] = Field(default_factory=list, max_length=12)

    @field_validator("technologies", mode="before")
    @classmethod
    def coerce_tech(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        if isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]
        return []


class ResumeAnalysis(StrictAIModel):
    career_target: str = Field(default="Full Stack Engineer", min_length=1, max_length=120)
    skills: list[ProfileSkill] = Field(default_factory=list, max_length=30)
    technologies: list[str] = Field(default_factory=list, max_length=30)
    projects: list[ResumeProject] = Field(default_factory=list, max_length=12)
    relevant_experience: list[str] = Field(default_factory=list, max_length=8)
    knowledge_areas: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("relevant_experience", mode="before")
    @classmethod
    def coerce_experience(cls, v):
        if isinstance(v, str):
            return [v.strip()] if v.strip() else []
        if isinstance(v, dict):
            parts = [str(v.get(k, "")) for k in ("role", "title", "company", "description") if v.get(k)]
            joined = " - ".join(parts).strip()
            return [joined] if joined else []
        if isinstance(v, list):
            items = []
            for item in v:
                if isinstance(item, str):
                    if item.strip():
                        items.append(item.strip())
                elif isinstance(item, dict):
                    parts = [str(item.get(k, "")) for k in ("role", "title", "company", "description") if item.get(k)]
                    joined = " - ".join(parts).strip()
                    if joined:
                        items.append(joined)
            return items[:8]
        return []

    @field_validator("technologies", "knowledge_areas", mode="before")
    @classmethod
    def coerce_string_list(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        if isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]
        return []


class AIQuizQuestion(StrictAIModel):
    topic: str = Field(min_length=1, max_length=100)
    concept: str = Field(min_length=1, max_length=140)
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    question: str = Field(min_length=4, max_length=1000)
    options: list[str] = Field(min_length=4, max_length=4)
    correct_answer: int = Field(default=0, ge=0, le=3)
    explanation: str = Field(default="Review this concept for more details.", min_length=1, max_length=1200)

    @model_validator(mode="before")
    @classmethod
    def handle_question_aliases(cls, data):
        if isinstance(data, dict):
            if "question" not in data:
                for alias in ("prompt", "question_text", "text", "q"):
                    if alias in data and str(data[alias]).strip():
                        data["question"] = str(data[alias]).strip()
                        break
            if "concept" not in data or not str(data.get("concept", "")).strip():
                data["concept"] = data.get("topic", "Core Fundamentals")
            if "topic" not in data or not str(data.get("topic", "")).strip():
                data["topic"] = "General"
            if "correct_answer" not in data:
                for alias in ("answer", "answer_index", "correct", "correct_option"):
                    if alias in data and data[alias] is not None:
                        data["correct_answer"] = data[alias]
                        break
            if isinstance(data.get("options"), dict):
                data["options"] = list(data["options"].values())
        return data

    @field_validator("difficulty", mode="before")
    @classmethod
    def coerce_difficulty(cls, v):
        val = str(v or "").lower().strip()
        if "easy" in val:
            return "easy"
        if "hard" in val:
            return "hard"
        return "medium"

    @field_validator("options", mode="before")
    @classmethod
    def coerce_options(cls, v):
        if isinstance(v, list):
            opts = [str(x).strip() for x in v if str(x).strip()]
            if len(opts) == 4:
                return opts
            if len(opts) > 4:
                return opts[:4]
            while len(opts) < 4:
                opts.append(f"Option {chr(65 + len(opts))}")
            return opts
        return ["Option A", "Option B", "Option C", "Option D"]

    @field_validator("correct_answer", mode="before")
    @classmethod
    def coerce_correct_answer(cls, v):
        if isinstance(v, str):
            v_clean = v.strip().upper()
            mapping = {"A": 0, "B": 1, "C": 2, "D": 3}
            if v_clean in mapping:
                return mapping[v_clean]
        try:
            val = int(v)
            return max(0, min(3, val))
        except (ValueError, TypeError):
            return 0

    @field_validator("explanation", mode="before")
    @classmethod
    def coerce_explanation(cls, v):
        text = str(v or "").strip()
        return text if text else "Review this concept for more details."


def _flatten_questions(items):
    flat = []
    if not isinstance(items, (list, tuple)):
        if isinstance(items, dict):
            return [items]
        return []
    for item in items:
        if isinstance(item, (list, tuple)):
            flat.extend(_flatten_questions(item))
        elif isinstance(item, dict):
            flat.append(item)
    return flat


class QuizGeneration(StrictAIModel):
    questions: list[AIQuizQuestion] = Field(default_factory=list, min_length=1, max_length=25)

    @model_validator(mode="before")
    @classmethod
    def handle_root_questions(cls, data):
        if isinstance(data, list):
            data = {"questions": data}
        if isinstance(data, dict):
            if "questions" not in data:
                for key in ("quiz", "items", "data", "results"):
                    if key in data and isinstance(data[key], (list, dict)):
                        data["questions"] = data[key]
                        break
                if "questions" not in data and any(k in data for k in ("topic", "question", "prompt")):
                    data["questions"] = [data]
            
            raw_q = data.get("questions")
            if isinstance(raw_q, dict):
                data["questions"] = [raw_q]
            elif isinstance(raw_q, list):
                data["questions"] = _flatten_questions(raw_q)
            else:
                data["questions"] = []
        return data


class PrioritySkill(StrictAIModel):
    skill: str = Field(min_length=1, max_length=100)
    priority: Literal["high", "medium", "low"] = "medium"
    reason: str = Field(min_length=1, max_length=500)
    next_topics: list[str] = Field(default_factory=list, max_length=6)
    practice: str = Field(default="", max_length=500)
    needs_reassessment: bool = False

    @field_validator("priority", mode="before")
    @classmethod
    def coerce_priority(cls, v):
        val = str(v or "").lower().strip()
        if "high" in val:
            return "high"
        if "low" in val:
            return "low"
        return "medium"

    @field_validator("next_topics", mode="before")
    @classmethod
    def coerce_next_topics(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        if isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]
        return []

    @field_validator("practice", mode="before")
    @classmethod
    def coerce_practice(cls, v):
        if isinstance(v, list):
            return "; ".join(str(x) for x in v)
        return str(v or "")


class LearningRecommendations(StrictAIModel):
    priority_skills: list[PrioritySkill] = Field(default_factory=list, max_length=12)
    next_focus: list[str] = Field(default_factory=list, max_length=16)
    reinforce: list[str] = Field(default_factory=list, max_length=16)
    next_topics: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("priority_skills", mode="before")
    @classmethod
    def coerce_priority_skills(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, dict):
            return [v]
        return []

    @field_validator("next_focus", "reinforce", "next_topics", mode="before")
    @classmethod
    def coerce_rec_lists(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()][:16]
        if isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()][:16]
        return []
