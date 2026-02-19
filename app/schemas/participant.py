from pydantic import BaseModel, EmailStr
from uuid import UUID


class ParticipantCreate(BaseModel):
    challenge_id: UUID
    participant_code: str
    email: EmailStr
    name: str
    college: str
    state: str


class ParticipantResponse(BaseModel):
    id: UUID
    challenge_id: UUID
    participant_code: str
    email: EmailStr
    name: str
    college: str
    state: str
    account_status: str

    class Config:
        from_attributes = True
