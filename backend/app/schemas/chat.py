from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    current_topic: str = "your current roadmap topic"
    career_target: str = "Full Stack Engineer"
    weak_gaps: list[str] = []
    user_id: str | None = None
