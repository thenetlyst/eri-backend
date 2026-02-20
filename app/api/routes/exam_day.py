import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.exam_day import ExamDay
from app.schemas.exam_day import ExamDayCreate, ExamDayResponse
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=ExamDayResponse)
def create_exam_day(
    payload: ExamDayCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exam_day = ExamDay(
        id=uuid.uuid4(),
        challenge_id=payload.challenge_id,
        day_number=payload.day_number,
        window_start=payload.window_start,
        window_end=payload.window_end,
        grace_seconds=payload.grace_seconds,
    )

    db.add(exam_day)
    db.commit()
    db.refresh(exam_day)

    return exam_day