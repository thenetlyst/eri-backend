from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class ExamDayCreate(BaseModel):
    challenge_id: UUID
    day_number: int
    window_start: datetime
    window_end: datetime
    grace_seconds: int = 10


class ExamDayResponse(BaseModel):
    id: UUID
    challenge_id: UUID
    day_number: int
    window_start: datetime
    window_end: datetime
    grace_seconds: int
    is_force_locked: bool

    class Config:
        from_attributes = True