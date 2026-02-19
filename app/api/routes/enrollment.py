from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.registration_application import RegistrationApplication
from app.models.participant import Participant
from app.models.user import User
from app.schemas.enrollment import EnrollmentResponse

router = APIRouter(tags=["Enrollment"])


@router.post("/enroll", response_model=EnrollmentResponse)
def enroll(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    email = current_user.email.lower()

    # 1️⃣ Check registration exists
    registration = (
        db.query(RegistrationApplication)
        .filter(RegistrationApplication.email == email)
        .first()
    )

    if not registration:
        raise HTTPException(
            status_code=403,
            detail="Email not registered for this challenge."
        )

    # 2️⃣ If already enrolled, return existing participant
    existing_participant = (
        db.query(Participant)
        .filter(
            Participant.challenge_id == registration.challenge_id,
            Participant.user_id == current_user.id,
        )
        .first()
    )

    if existing_participant:
        return EnrollmentResponse(
            participant_id=existing_participant.id,
            participant_code=existing_participant.participant_code,
            challenge_id=existing_participant.challenge_id,
        )

    # 3️⃣ Create participant
    participant = Participant(
        user_id=current_user.id,
        challenge_id=registration.challenge_id,
        participant_code=registration.participant_code,
        state=registration.state,
        college=registration.college,
    )

    db.add(participant)

    # 4️⃣ Mark registration as enrolled
    registration.enrolled = True

    db.commit()
    db.refresh(participant)

    return EnrollmentResponse(
        participant_id=participant.id,
        participant_code=participant.participant_code,
        challenge_id=participant.challenge_id,
    )
