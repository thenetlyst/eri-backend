from pydantic import BaseModel


class ChallengeCreate(BaseModel):
    name: str

from uuid import UUID

class ChallengeResponse(BaseModel):
    id: UUID
    name: str
    status: str

    class Config:
        from_attributes = True

        
