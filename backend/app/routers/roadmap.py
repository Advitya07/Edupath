from fastapi import APIRouter
from app.schemas.roadmap import RoadmapRequest, ResourceRequest
from app.ai.chains.roadmap_chain import make_roadmap
from app.ai.vector.pinecone_client import find_resources

router = APIRouter(prefix="/roadmap", tags=["roadmap"])


@router.post("/generate")
async def generate(payload: RoadmapRequest):
    return make_roadmap(payload.career_target, payload.scores, payload.skills)


@router.post("/resources")
async def resources(payload: ResourceRequest):
    return {"topic": payload.topic, "resources": await find_resources(payload.topic), "practice_task": f"Build a small {payload.topic} feature and explain your design decisions."}
