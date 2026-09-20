from pydantic import BaseModel, Field


class QuizRequest(BaseModel):
    career_target: str
    skills: list[str] = []
    topic: str | None = None
    node_id: str | None = None
    previous_topics: list[str] = []
    user_id: str | None = None


class Answer(BaseModel):
    question_id: str
    selected_index: int = Field(ge=0, le=3)
    confidence: int = Field(ge=1, le=5)


class QuizSubmission(BaseModel):
    quiz_id: str
    answers: list[Answer]
    previous_scores: dict[str, float] = {}
    user_id: str | None = None
