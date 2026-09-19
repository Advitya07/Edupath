from pydantic import BaseModel


class RoadmapRequest(BaseModel):
    career_target: str
    scores: dict[str, float] = {}
    skills: list[str] = []


class ResourceRequest(BaseModel):
    topic: str
    career_target: str = "Full Stack Engineer"
