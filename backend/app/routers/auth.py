from uuid import uuid4
from fastapi import APIRouter, HTTPException
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
    extracted = analyze_resume(payload.resume_text)
    profile = {"user_id": user_id, **payload.model_dump(), **extracted}
    await db.upsert("profiles", {"user_id": user_id}, profile)
    user = await db.find_one("users", {"id": user_id})
    if user:
        await db.upsert("users", {"id": user_id}, {**user, "career_target": payload.career_target})
    return profile
