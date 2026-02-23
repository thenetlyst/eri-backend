import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    ForeignKey,
    Numeric,
    Integer,
    Boolean,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class ParticipantProgress(Base):
    __tablename__ = "participant_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    challenge_id = Column(
        UUID(as_uuid=True),
        ForeignKey("challenges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    participant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("participants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # -----------------------------------------
    # LEADERBOARD (Additive Final Score)
    # -----------------------------------------
    cumulative_score = Column(Numeric(10, 2), nullable=False, default=0)

    # -----------------------------------------
    # BASE PERFORMANCE TRACKING (Eligibility)
    # -----------------------------------------
    cumulative_base_effective_score = Column(
        Numeric(10, 2),
        nullable=False,
        default=0,
    )

    cumulative_base_max = Column(
        Numeric(10, 2),
        nullable=False,
        default=0,
    )

    # -----------------------------------------
    # Participation Tracking
    # -----------------------------------------
    days_completed = Column(Integer, nullable=False, default=0)
    attendance_count = Column(Integer, nullable=False, default=0)

    # -----------------------------------------
    # Bonus Eligibility Flag
    # -----------------------------------------
    eligible_for_bonus_next_day = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    last_updated = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint(
            "challenge_id",
            "participant_id",
            name="uq_progress_challenge_participant",
        ),
    )
