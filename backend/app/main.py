from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
async def parse_resume(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(400, "Upload a .pdf or .txt file")
    try:
        return analyze_resume(extract_text(file.filename, await file.read()))
    except Exception as exc:
        raise HTTPException(400, f"Could not read resume: {exc}")
