from pydantic import BaseModel
from uuid import UUID


class QuestionCreate(BaseModel):
    challenge_id: UUID
    exam_day_id: UUID
    question_order: int
    question_text: str

    option_a: str
    option_b: str
    option_c: str
    option_d: str

    correct_option: str
    weight: float
    difficulty: str

    allocated_time_seconds: int

    hint_text: str | None = None
    hint_penalty_percentage: int | None = None

    is_special: bool = False


class QuestionResponse(BaseModel):
    id: UUID
    challenge_id: UUID
    exam_day_id: UUID
    question_order: int
    question_text: str

    option_a: str
    option_b: str
    option_c: str
    option_d: str

    correct_option: str
    weight: float
    difficulty: str
    allocated_time_seconds: int
    is_special: bool

    class Config:
        from_attributes = True