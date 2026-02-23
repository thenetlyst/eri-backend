from pydantic import BaseModel
from uuid import UUID


class EnrollmentResponse(BaseModel):
    participant_id: UUID
    participant_code: str
    challenge_id: UUID
