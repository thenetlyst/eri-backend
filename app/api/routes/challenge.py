import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.challenge import Challenge
from app.models.exam_day import ExamDay
from app.schemas.challenge import ChallengeCreate, ChallengeResponse


router = APIRouter()


@router.post("/", response_model=ChallengeResponse)
def create_challenge(payload: ChallengeCreate, db: Session = Depends(get_db)):

    challenge = Challenge(
        id=uuid.uuid4(),
        name=payload.name
    )

    db.add(challenge)
    db.commit()
    db.refresh(challenge)

    # Auto-create 7 exam days
    base_date = datetime.utcnow()

    for day in range(1, 8):
        exam_day = ExamDay(
            id=uuid.uuid4(),
            challenge_id=challenge.id,
            day_number=day,
            window_start=base_date + timedelta(days=day),
            window_end=base_date + timedelta(days=day, hours=2),
            grace_seconds=10,
            is_force_locked=False
        )

        db.add(exam_day)

    db.commit()

    return challenge
