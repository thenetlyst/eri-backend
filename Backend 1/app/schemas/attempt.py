from pydantic import BaseModel
from uuid import UUID


class AttemptStartRequest(BaseModel):
    exam_day_id: UUID


class AttemptStartResponse(BaseModel):
    attempt_id: UUID
    allowed_duration_seconds: int
    special_unlocked: bool

    class Config:
        from_attributes = True
