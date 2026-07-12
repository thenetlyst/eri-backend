from pydantic import BaseModel
from uuid import UUID


# -----------------------------
# Create
# -----------------------------

class ParticipantCreate(BaseModel):
    challenge_id: UUID
    name: str
    college: str
    state: str
    graduation_year: int


# -----------------------------
# Response
# -----------------------------

class ParticipantResponse(BaseModel):
    id: UUID
    user_id: UUID
    challenge_id: UUID
    participant_code: str
    name: str
    college: str
    state: str
    graduation_year: int
    account_status: str

    class Config:
        from_attributes = True