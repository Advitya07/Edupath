from hashlib import sha256
from uuid import uuid4
from fastapi import APIRouter, HTTPException
from app.ai.llm import AIServiceError
from app.ai.service import ai_service
from app.database.mongodb import db
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse, ProfileRequest
from app.services.resume_service import analyze_resume
from app.utils.security import create_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
async def register(payload: RegisterRequest):
    if await db.find_one("users", {"email": payload.email}):
        raise HTTPException(409, "An account already exists for this email")
    user = {"id": str(uuid4()), "name": payload.name, "email": payload.email, "password": payload.password, "career_target": "Not selected"}
    await db.insert("users", user)
    return {"token": create_token(user["id"]), "user": {k: v for k, v in user.items() if k != "password"}}


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest):
    user = await db.find_one("users", {"email": payload.email})
    if not user or user["password"] != payload.password:
        raise HTTPException(401, "Invalid email or password")
    return {"token": create_token(user["id"]), "user": {k: v for k, v in user.items() if k != "password"}}


@router.post("/profile/{user_id}")
async def save_profile(user_id: str, payload: ProfileRequest):
    existing = await db.find_one("profiles", {"user_id": user_id}) or {}
    resume_text = payload.resume_text.strip()
    resume_hash = sha256(resume_text.encode("utf-8")).hexdigest() if resume_text else existing.get("resume_hash")
    profile_changed = (
        bool(resume_text and resume_hash != existing.get("resume_hash"))
        or payload.career_target != existing.get("career_target")
    )
    profile_version = int(existing.get("profile_version", 0)) + (1 if profile_changed else 0)
    deterministic = analyze_resume(resume_text) if resume_text else {"skills": [], "text_length": 0}
    fallback_skills = list(dict.fromkeys([*payload.skills, *deterministic["skills"]]))
    ai_status: dict = {"success": True}

    if resume_text and (profile_changed or existing.get("ai_status") != "ready" or not existing.get("skill_profile")):
        try:
            analyzed = await ai_service.analyze_resume(
                user_id,
                resume_text,
                payload.career_target,
                payload.skills,
                existing_profile={**existing, "experience_level": payload.experience_level},
            )
            skill_profile = analyzed["skills"]
            technologies = analyzed["technologies"]
            projects = analyzed["projects"]
            relevant_experience = analyzed["relevant_experience"]
            knowledge_areas = analyzed["knowledge_areas"]
            skills = list(dict.fromkeys([*(item["name"] for item in skill_profile), *fallback_skills]))
        except AIServiceError as exc:
            # The non-AI parser is still saved, so a failed local model never loses
            # the uploaded learner signal or overwrites a prior valid profile.
            ai_status = exc.as_dict()
            skill_profile = [
                {"name": skill, "level": 5, "evidence": ["Detected in uploaded résumé"]}
                for skill in fallback_skills
            ]
            technologies = existing.get("technologies", [])
            projects = existing.get("projects", [])
            relevant_experience = existing.get("relevant_experience", [])
            knowledge_areas = existing.get("knowledge_areas", [])
            skills = fallback_skills
    else:
        skill_profile = existing.get("skill_profile") or [
            {"name": skill, "level": 5, "evidence": ["Provided by learner"]}
            for skill in fallback_skills
        ]
        technologies = existing.get("technologies", [])
        projects = existing.get("projects", [])
        relevant_experience = existing.get("relevant_experience", [])
        knowledge_areas = existing.get("knowledge_areas", [])
        skills = list(dict.fromkeys([*(item["name"] for item in skill_profile), *fallback_skills]))

    profile = {
        **existing,
        "user_id": user_id,
        "career_target": payload.career_target,
        "experience_level": payload.experience_level,
        "skills": skills,
        "skill_profile": skill_profile,
        "technologies": technologies,
        "projects": projects,
        "relevant_experience": relevant_experience,
        "knowledge_areas": knowledge_areas,
        "resume_hash": resume_hash,
        "text_length": len(resume_text) if resume_text else existing.get("text_length", 0),
        "profile_version": profile_version,
        "ai_status": "ready" if ai_status.get("success") else "unavailable",
    }
    await db.upsert("profiles", {"user_id": user_id}, profile)
    user = await db.find_one("users", {"id": user_id})
    if user:
        await db.upsert("users", {"id": user_id}, {**user, "career_target": payload.career_target})
    return {**profile, "ai": ai_status}
