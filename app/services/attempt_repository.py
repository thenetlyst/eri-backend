from sqlalchemy.orm import Session

from app.models.challenge import Challenge
from app.models.exam_day import ExamDay
from app.models.participant import Participant
from app.models.participant_progress import ParticipantProgress


class AttemptRepository:

    @staticmethod
    def get_exam_day(
        db: Session,
        exam_day_id: int,
    ):
        return (
            db.query(ExamDay)
            .filter(ExamDay.id == exam_day_id)
            .first()
        )

    @staticmethod
    def get_challenge(
        db: Session,
        challenge_id,
    ):
        return (
            db.query(Challenge)
            .filter(Challenge.id == challenge_id)
            .first()
        )

    @staticmethod
    def get_participant(
        db: Session,
        *,
        user_id,
        challenge_id,
    ):
        return (
            db.query(Participant)
            .filter(
                Participant.user_id == user_id,
                Participant.challenge_id == challenge_id,
            )
            .first()
        )

    @staticmethod
    def get_progress(
        db: Session,
        *,
        participant_id,
        challenge_id,
    ):
        return (
            db.query(ParticipantProgress)
            .filter(
                ParticipantProgress.challenge_id == challenge_id,
                ParticipantProgress.participant_id == participant_id,
            )
            .first()
        )