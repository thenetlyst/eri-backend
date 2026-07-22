from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, case, func
from sqlalchemy.orm import Session

from app.models.challenge import Challenge, ChallengeStatus
from app.models.exam_day import ExamDay
from app.models.participant import Participant, AccountStatus
from app.models.participant_progress import ParticipantProgress


@dataclass(slots=True, frozen=True)
class StartAttemptContext:
    exam_day_id: UUID
    challenge_id: UUID
    participant_id: UUID

    window_start: datetime
    window_end: datetime
    is_force_locked: bool

    challenge_status: ChallengeStatus
    account_status: AccountStatus

    days_completed: int
    eligible_for_bonus_next_day: bool


class AttemptRepository:

    @staticmethod
    def get_start_attempt_context(
        db: Session,
        exam_day_id: UUID,
        user_id: UUID,
    ) -> StartAttemptContext | None:
        """
        Loads everything required to start an attempt in a single query.

        Returns None if the user is not eligible to start this exam.

        This intentionally combines:
            ExamDay
            Challenge
            Participant
            ParticipantProgress

        into one optimized lookup.
        """

        stmt = (
            select(
                ExamDay.id.label("exam_day_id"),
                Challenge.id.label("challenge_id"),
                Participant.id.label("participant_id"),

                ExamDay.window_start,
                ExamDay.window_end,
                ExamDay.is_force_locked,

                Challenge.status.label("challenge_status"),
                Participant.account_status.label("account_status"),

                func.coalesce(
                    ParticipantProgress.days_completed,
                    0,
                ).label("days_completed"),

                func.coalesce(
                    ParticipantProgress.eligible_for_bonus_next_day,
                    False,
                ).label("eligible_for_bonus_next_day"),
            )
            .join(
                Challenge,
                Challenge.id == ExamDay.challenge_id,
            )
            .join(
                Participant,
                (Participant.challenge_id == Challenge.id)
                &
                (Participant.user_id == user_id),
            )
            .outerjoin(
                ParticipantProgress,
                (ParticipantProgress.participant_id == Participant.id)
                &
                (ParticipantProgress.challenge_id == Challenge.id),
            )
            .where(
                ExamDay.id == exam_day_id,
            )
        )

        row = db.execute(stmt).one_or_none()

        if row is None:
            return None

        return StartAttemptContext(
            exam_day_id=row.exam_day_id,
            challenge_id=row.challenge_id,
            participant_id=row.participant_id,

            window_start=row.window_start,
            window_end=row.window_end,
            is_force_locked=row.is_force_locked,

            challenge_status=row.challenge_status,
            account_status=row.account_status,

            days_completed=row.days_completed,
            eligible_for_bonus_next_day=row.eligible_for_bonus_next_day,
        )