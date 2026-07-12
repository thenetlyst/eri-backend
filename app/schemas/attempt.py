from pydantic import BaseModel
from uuid import UUID
from ._strict import StrictRequest

class AttemptStartRequest(StrictRequest):
    exam_day_id: UUID


class AttemptStartResponse(BaseModel):
    attempt_id: UUID
    allowed_duration_seconds: int
    special_unlocked: bool

    class Config:
        from_attributes = True
