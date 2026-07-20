from sqlalchemy.orm import Session

from app.models.challenge import Challenge
from app.models.exam_day import ExamDay
from app.models.participant import Participant
from app.models.participant_progress import ParticipantProgress
from app.models.user import User


class AttemptRepository:

    @staticmethod
    def load_start_data(
        db: Session,
        *,
        current_user: User,
        exam_day_id: int,
    ):
        """
        Temporary repository.

        Initial implementation intentionally mirrors the existing
        endpoint behaviour exactly.
        """
        raise NotImplementedError