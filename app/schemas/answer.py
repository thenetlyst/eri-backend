from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from ._strict import StrictRequest


class AnswerSubmitRequest(StrictRequest):
    question_id: UUID
    selected_option: Optional[str] = None   # 🔥 FIXED
    hint_used: bool = False


class AnswerSubmitResponse(BaseModel):
    is_correct: bool
    raw_score: float
    effective_score: float
    total_hints_used: int