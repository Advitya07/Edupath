from contextlib import asynccontextmanager
from hashlib import sha256
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.ai.llm import AIServiceError
from app.ai.service import ai_service
from app.database.mongodb import db
from app.utils.file_parser import extract_text
from app.services.resume_service import analyze_resume
from app.routers import auth, assessment, roadmap, chat, admin


@asynccontextmanager
async def lifespan(_: FastAPI):
    await db.connect()
    yield
    await db.close()


app = FastAPI(title="EduPath API", version="0.1.0", lifespan=lifespan)
# Vite selects the next available port (for example 5174) when 5173 is busy.
# Permit only local browser origins across those development ports; deployed
# applications should replace this with their explicit production origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
for router in (auth.router, assessment.router, roadmap.router, chat.router, admin.router):
    app.include_router(router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "mode": "demo" if db.db is None else "connected"}


@app.post("/api/resume/parse")
async def parse_resume(
    file: UploadFile = File(...),
    user_id: str | None = Form(None),
    career_target: str | None = Form(None),
):
    if not file.filename or not file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(400, "Upload a .pdf or .txt file")
    try:
        text = extract_text(file.filename, await file.read())
        extracted = analyze_resume(text)
        response = {**extracted, "resume_text": text, "ai": {"success": True}}
        if not (user_id and career_target):
            return response
        existing = await db.find_one("profiles", {"user_id": user_id}) or {}
        resume_hash = sha256(text.encode("utf-8")).hexdigest()
        if (
            existing.get("resume_hash") == resume_hash
            and existing.get("career_target") == career_target
            and existing.get("ai_status") == "ready"
        ):
            return {**response, "skills": existing.get("skills", extracted["skills"]), "ai": {"success": True}}
        try:
            analyzed = await ai_service.analyze_resume(
                user_id, text, career_target, extracted["skills"], existing_profile=existing
            )
            skills = list(dict.fromkeys([*(item["name"] for item in analyzed["skills"]), *extracted["skills"]]))
            draft = {
                **existing,
                "user_id": user_id,
                "career_target": career_target,
                "skills": skills,
                "skill_profile": analyzed["skills"],
                "technologies": analyzed["technologies"],
                "projects": analyzed["projects"],
                "relevant_experience": analyzed["relevant_experience"],
                "knowledge_areas": analyzed["knowledge_areas"],
                "resume_hash": resume_hash,
                "text_length": len(text),
                "profile_version": int(existing.get("profile_version", 0)) + 1,
                "ai_status": "ready",
            }
            await db.upsert("profiles", {"user_id": user_id}, draft)
            return {**response, "skills": skills, "ai": {"success": True}}
        except AIServiceError as exc:
            # The upload itself remains usable; profile save can retry the local model.
            return {**response, "ai": exc.as_dict()}
    except Exception as exc:
        raise HTTPException(400, f"Could not read resume: {exc}")
