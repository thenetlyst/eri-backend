import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_db
from app.models.participant import Participant
from app.schemas.participant import ParticipantCreate, ParticipantResponse
from app.core.exceptions import ConflictException


router = APIRouter()


@router.post("/", response_model=ParticipantResponse)
def create_participant(
    payload: ParticipantCreate,
    db: Session = Depends(get_db),
):

    participant = Participant(
        id=uuid.uuid4(),
        challenge_id=payload.challenge_id,
        participant_code=payload.participant_code,
        email=payload.email,
        name=payload.name,
        college=payload.college,
        state=payload.state,
        account_status="ACTIVE",  # make explicit
    )

    db.add(participant)

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()

        error_text = str(e.orig)

        if "participants_email_key" in error_text:
            raise ConflictException("Email already registered")

        if "participants_participant_code_key" in error_text:
            raise ConflictException("Participant code already exists")

        raise ConflictException("Participant already exists")

    db.refresh(participant)

    return participant
