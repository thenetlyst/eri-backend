import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_db, get_current_user
from app.models.participant import Participant
from app.models.user import User
from app.schemas.participant import ParticipantCreate, ParticipantResponse
from app.core.exceptions import ConflictException


router = APIRouter()


@router.post("/", response_model=ParticipantResponse)
def create_participant(
    payload: ParticipantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 🔒 HARD BLOCK — disable unsafe endpoint completely
    raise HTTPException(
        status_code=403,
        detail="Direct participant creation is disabled. Use enrollment."
    )

    # (This code remains for future rollback / debugging, but never executes)
    participant = Participant(
        id=uuid.uuid4(),
        user_id=current_user.id,
        challenge_id=payload.challenge_id,
        participant_code="TEMP_BLOCKED",
        name=payload.name,
        college=payload.college,
        state=payload.state,
        graduation_year=payload.graduation_year,
        account_status="ACTIVE",
    )

    db.add(participant)

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()

        error_text = str(e.orig)

        if "uq_participant_code" in error_text:
            raise ConflictException("Participant code already exists")

        if "uq_user_challenge" in error_text:
            raise ConflictException("User already registered for this challenge")

        raise ConflictException("Participant already exists")

    db.refresh(participant)

    return participant