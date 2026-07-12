from pydantic import BaseModel
from uuid import UUID
from typing import Optional, Dict, Any
from ._strict import StrictRequest

class QuestionCreate(StrictRequest):
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
# ⭐ NEW
    content_json: Optional[Dict[str, Any]] = None

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

 # ⭐ NEW
    content_json: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

    