"""Task-specific prompts layered over the single Ollama provider."""
from __future__ import annotations

import json
import re
from uuid import uuid4

from app.ai.llm import llm, AIServiceError
from app.ai.schemas import LearningRecommendations, QuizGeneration, ResumeAnalysis


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _compact_profile(profile: dict) -> dict:
    skill_profile = profile.get("skill_profile") or [
        {"name": skill, "level": 5} for skill in profile.get("skills", [])
    ]
    return {
        "career_target": profile.get("career_target", "Not selected"),
        "experience_level": profile.get("experience_level", "Early career"),
        "skills": [
            {"name": item.get("name"), "level": item.get("level", 5)}
            for item in skill_profile[:20]
            if item.get("name")
        ],
        "technologies": profile.get("technologies", [])[:20],
        "knowledge_areas": profile.get("knowledge_areas", [])[:20],
    }


def _present_in_source(value: str, source: str) -> bool:
    normalized_value = re.sub(r"[^\w\s]", " ", value.lower()).strip()
    normalized_source = re.sub(r"[^\w\s]", " ", source.lower())
    if not normalized_value:
        return False
    if normalized_value in normalized_source:
        return True
    tokens = [t for t in normalized_value.split() if len(t) >= 3 and t not in {"and", "the", "for", "with"}]
    return any(t in normalized_source for t in tokens)


class LearningAIService:
    async def analyze_resume(
        self,
        user_id: str,
        resume_text: str,
        career_goal: str,
        manually_entered_skills: list[str] | None = None,
        existing_profile: dict | None = None,
    ) -> dict:
        """Extract only claims grounded in this resume; raw text is not retained afterwards."""
        learner_context = _json({
            "experience_level": (existing_profile or {}).get("experience_level"),
            "skills": manually_entered_skills or [],
        })
        prompt = f"""You are extracting a learner profile for EduPath.
Return only strict JSON. Do not infer, embellish, or add skills, projects, or experience that are not explicitly supported by the resume.
For every skill, include short evidence copied or closely paraphrased from the resume. Use skill level 1-10 only as an approximate confidence from the evidence.
The requested career target is {career_goal!r}; preserve it unless the resume explicitly states a different target.

Existing learner context (may be used only when explicitly provided here): {learner_context}

Resume:\n{resume_text[:24000]}

Required JSON object keys: career_target, skills, technologies, projects, relevant_experience, knowledge_areas.
Each skill has name, level, evidence. Each project has name, technologies."""
        analysis = await llm.invoke_structured(prompt, ResumeAnalysis)
        allowed_source = "\n".join([resume_text, *(manually_entered_skills or [])])
        supported_skills = [skill for skill in analysis.skills if _present_in_source(skill.name, allowed_source)]
        supported_technologies = [
            technology for technology in analysis.technologies if _present_in_source(technology, allowed_source)
        ]
        supported_projects = [
            project
            for project in analysis.projects
            if _present_in_source(project.name, resume_text)
        ]
        return {
            "user_id": user_id,
            "career_target": career_goal,
            "skills": [skill.model_dump() for skill in supported_skills],
            "technologies": supported_technologies,
            "projects": [project.model_dump() for project in supported_projects],
            "relevant_experience": [
                experience for experience in analysis.relevant_experience if _present_in_source(experience, resume_text)
            ],
            "knowledge_areas": analysis.knowledge_areas,
        }

    async def generate_initial_quiz(self, profile: dict, career_goal: str) -> list[dict]:
        context = _compact_profile({**profile, "career_target": career_goal})
        prompt = f"""Create 10 personalized four-option multiple-choice diagnostic questions for an EduPath learner.
Return only strict JSON: {{"questions": [...]}}.
You MUST generate between 6 and 10 questions in the "questions" list. Do NOT return only one question.
Cover the learner's target career ({career_goal}) and their skills with a useful spread of easy, medium, and hard questions.
correct_answer is the zero-based index of the correct option (0, 1, 2, or 3). Never mention the learner, CV, or JSON in the question text.
Learner profile: {_json(context)}

Every item in the "questions" list must contain:
- topic: specific topic or technology
- concept: the concept being tested
- difficulty: easy, medium, or hard
- question: clear question text
- options: list of exactly 4 options
- correct_answer: 0, 1, 2, or 3
- explanation: brief explanation"""
        try:
            batch = await llm.invoke_structured(prompt, QuizGeneration)
            questions = self._quiz_records(batch)
        except AIServiceError:
            questions = self._fallback_quiz(career_goal, profile.get("skills", []))

        if len(questions) < 5:
            questions = self._pad_quiz(career_goal, questions, target_count=8)
        return questions

    async def generate_reassessment_quiz(
        self,
        profile: dict,
        skill_scores: dict[str, float],
        previous_quiz_results: dict,
        current_weak_topics: list[str],
        selected_topic: str | None = None,
    ) -> list[dict]:
        context = {
            "profile": _compact_profile(profile),
            "skill_scores": skill_scores,
            "weak_topics": current_weak_topics[:10],
            "selected_topic": selected_topic,
            "recent_result": previous_quiz_results,
        }
        topic_focus = f"with special focus on {selected_topic}" if selected_topic else f"focusing on weak areas: {', '.join(current_weak_topics[:3])}"
        prompt = f"""Create 10 personalized four-option EduPath reassessment MCQs {topic_focus}.
Return only strict JSON: {{"questions": [...]}}.
You MUST generate between 6 and 10 questions in the "questions" list. Do NOT return only one question.
Use this learner state: {_json(context)}
Favor weak or selected topics (about 70%), include current learning topics (about 20%), and retain some stronger-topic reinforcement (about 10%).
Every questions item must contain: topic, concept, difficulty (easy|medium|hard), question, options (exactly 4), correct_answer (0-3), explanation."""
        try:
            batch = await llm.invoke_structured(prompt, QuizGeneration)
            questions = self._quiz_records(batch)
        except AIServiceError:
            career = profile.get("career_target", "Full Stack Engineer")
            focus = selected_topic or (current_weak_topics[0] if current_weak_topics else "Fundamentals")
            questions = self._fallback_quiz(career, [focus, *(profile.get("skills", []))])

        if len(questions) < 5:
            career = profile.get("career_target", "Full Stack Engineer")
            questions = self._pad_quiz(selected_topic or career, questions, target_count=8)
        return questions

    @classmethod
    def _fallback_quiz(cls, career: str, skills: list[str]) -> list[dict]:
        """Generate reliable foundational diagnostic questions if the model is unreachable."""
        target_skills = [s for s in skills if s] or [career, "Fundamentals", "Architecture", "Security"]
        questions = []
        templates = [
            ("What is a primary architectural principle of {topic}?", [
                "Modular decomposition and separation of concerns",
                "Monolithic coupling of state and UI",
                "Randomizing execution order for performance",
                "Ignoring error boundaries in production",
            ], 0, "Modular architecture allows maintainability and testability."),
            ("When troubleshooting performance in {topic}, which approach is most effective?", [
                "Profiling bottlenecks with telemetry before optimizing",
                "Immediately rewriting the codebase from scratch",
                "Disabling logging and error checks",
                "Increasing memory without measuring usage",
            ], 0, "Profiling provides evidence-based insight into actual bottlenecks."),
            ("How is state or data integrity typically maintained in {topic}?", [
                "Using validated transactions, immutability, or schema constraints",
                "Allowing unvalidated concurrent writes across threads",
                "Storing secrets directly in client-side code",
                "Bypassing data validation layers during peak traffic",
            ], 0, "Schema validation and transactional integrity prevent corrupted states."),
            ("In production environments, what is the best practice for {topic} error handling?", [
                "Graceful degradation with structured logging and user feedback",
                "Silently swallowing exceptions without logging",
                "Terminating the entire host process on minor warnings",
                "Displaying raw internal stack traces to end users",
            ], 0, "Structured logging enables debugging while graceful degradation protects UX."),
            ("What is a core trade-off when scaling {topic} systems?", [
                "Balancing consistency, availability, and latency across boundaries",
                "Assuming zero network latency and infinite bandwidth",
                "Never partitioning data or using caches",
                "Replacing all persistent storage with transient memory",
            ], 0, "Distributed systems must balance consistency and latency trade-offs."),
        ]
        for i, (tmpl, opts, ans, exp) in enumerate(templates):
            skill = target_skills[i % len(target_skills)]
            questions.append({
                "id": str(uuid4()),
                "topic": skill,
                "concept": f"{skill} Core",
                "difficulty": "medium" if i % 2 == 0 else "hard",
                "prompt": tmpl.format(topic=skill),
                "options": opts,
                "answer_index": ans,
                "explanation": exp,
            })
        return questions

    @classmethod
    def _pad_quiz(cls, career: str, existing_questions: list[dict], target_count: int = 8) -> list[dict]:
        fallback = cls._fallback_quiz(career, [career])
        padded = list(existing_questions)
        for q in fallback:
            if len(padded) >= target_count:
                break
            if q.get("prompt") not in {x.get("prompt") for x in padded}:
                padded.append(q)
        return padded

    @staticmethod
    def _quiz_records(batch: QuizGeneration) -> list[dict]:
        return [
            {
                "id": str(uuid4()),
                "topic": question.topic,
                "concept": question.concept,
                "difficulty": question.difficulty,
                "prompt": question.question,
                "options": question.options,
                "answer_index": question.correct_answer,
                "explanation": question.explanation,
            }
            for question in batch.questions[:10]
        ]

    async def analyze_post_quiz_performance(
        self,
        user_profile: dict,
        current_skill_scores: dict[str, float],
        historical_skill_scores: dict,
        recent_quiz: dict,
        roadmap_state: dict | None,
    ) -> dict:
        compact_roadmap = [
            {"topic": node.get("topic"), "status": node.get("status"), "mastery": node.get("mastery")}
            for node in (roadmap_state or {}).get("nodes", [])[:20]
        ]
        context = {
            "career": user_profile.get("career_target", "Not selected"),
            "skill_scores": current_skill_scores,
            "history_summary": historical_skill_scores,
            "recent_quiz": recent_quiz,
            "roadmap": compact_roadmap,
        }
        prompt = f"""You are an EduPath learning-planning assistant. Return only strict JSON for the learner state below.
Prioritize weak or regressing skills, reinforce learning skills, and recommend concrete concepts and practice. Do not invent resources, URLs, graph nodes, or scores.
Learner state: {_json(context)}
Required keys (arrays must be JSON lists, never empty strings):
- priority_skills: list of objects with (skill, priority: high|medium|low, reason, next_topics: list of strings, practice, needs_reassessment)
- next_focus: list of topic strings
- reinforce: list of topic strings
- next_topics: list of topic strings"""
        recommendations = await llm.invoke_structured(prompt, LearningRecommendations)
        return recommendations.model_dump()

    async def generate_chat_response(self, user_context: dict, message: str, recent_history: list[dict]) -> str:
        prompt = f"""You are EduPath's concise, encouraging learning mentor. Answer the learner's question using their current context.
Do not claim that you reviewed information absent from the context. If a request conflicts with the current learning priority, explain the trade-off and suggest a practical next step.
Learner context: {_json(user_context)}
Recent conversation: {_json(recent_history[-6:])}
Learner question: {message}
Return normal conversational text only, with no markdown table and no JSON."""
        return await llm.invoke(prompt)


ai_service = LearningAIService()
