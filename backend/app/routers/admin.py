from fastapi import APIRouter
from app.database.mongodb import db

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/overview")
async def overview():
    users = await db.find_all("users")
    progress = await db.find_all("progress")
    average = round(sum(p.get("overall", 0) for p in progress) / len(progress), 1) if progress else 0
    display_users = [{k: v for k, v in user.items() if k != "password"} for user in users]
    return {"stats": {"learners": len(users), "assessments": len(progress), "average_mastery": average, "at_risk": sum(1 for p in progress if p.get("overall", 0) < 55)}, "users": display_users}
