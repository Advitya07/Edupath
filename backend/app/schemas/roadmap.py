from pydantic import BaseModel


class RoadmapRequest(BaseModel):
    career_target: str
    scores: dict[str, float] = {}
    skills: list[str] = []
    user_id: str | None = None


class ResourceRequest(BaseModel):
    topic: str
    career_target: str = "Full Stack"
    node_id: str | None = None
