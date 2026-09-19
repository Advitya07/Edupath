from datetime import datetime, timezone
from fastapi import APIRouter
from app.schemas.roadmap import RoadmapRequest, ResourceRequest
from app.ai.chains.roadmap_chain import apply_recommendations, make_roadmap
from app.database.mongodb import db
from app.ai.vector.pinecone_client import find_resources

router = APIRouter(prefix="/roadmap", tags=["roadmap"])


@router.post("/generate")
async def generate(payload: RoadmapRequest):
    if not payload.user_id:
        return make_roadmap(payload.career_target, payload.scores, payload.skills)
    state = await db.find_one("skill_states", {"user_id": payload.user_id}) or {}
    scores = state.get("scores") or payload.scores
    roadmap = await db.find_one("roadmaps", {"user_id": payload.user_id})
    recommendation_record = await db.find_one("recommendations", {"user_id": payload.user_id}) or {}
    recommendations = recommendation_record.get("recommendations")
    if roadmap and roadmap.get("career_target") == payload.career_target and roadmap.get("skill_state_version") == state.get("version", 0):
        return roadmap
    if roadmap and roadmap.get("career_target") == payload.career_target:
        next_roadmap = apply_recommendations(roadmap, scores, recommendations)
        roadmap_version = int(roadmap.get("roadmap_version", 0)) + 1
    else:
        next_roadmap = apply_recommendations(
            make_roadmap(payload.career_target, scores, payload.skills), scores, recommendations
        )
        roadmap_version = 1
    next_roadmap.update({
        "user_id": payload.user_id,
        "skill_state_version": state.get("version", 0),
        "roadmap_version": roadmap_version,
        "recommendations": recommendations or {},
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })
    await db.upsert("roadmaps", {"user_id": payload.user_id}, next_roadmap)
    return next_roadmap


@router.post("/resources")
async def resources(payload: ResourceRequest):
    return {"topic": payload.topic, "resources": await find_resources(payload.topic), "practice_task": f"Build a small {payload.topic} feature and explain your design decisions."}
