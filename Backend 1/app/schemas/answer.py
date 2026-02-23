from pydantic import BaseModel
from uuid import UUID


class AnswerSubmitRequest(BaseModel):
    question_id: UUID
    selected_option: str
    hint_used: bool = False


class AnswerSubmitResponse(BaseModel):
    is_correct: bool
    raw_score: float
    effective_score: float
    total_hints_used: int
