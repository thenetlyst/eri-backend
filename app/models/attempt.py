import uuid
import enum

from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    Boolean,
    ForeignKey,
    DateTime,
    Enum,
    String,
    UniqueConstraint,
    Index,
    JSON,  # ⭐ snapshot stays JSON for now
)

from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class AttemptStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    MISSED = "MISSED"


class Attempt(Base):
    __tablename__ = "attempts"

    __table_args__ = (
        UniqueConstraint(
            "participant_id",
            "exam_day_id",
            name="uq_participant_exam_day",
        ),
        Index("idx_attempt_exam_day", "exam_day_id"),
        Index("idx_attempt_participant", "participant_id"),
        Index("idx_attempt_challenge", "challenge_id"),
        Index("idx_attempt_status_started", "status", "started_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    challenge_id = Column(
        UUID(as_uuid=True),
        ForeignKey("challenges.id", ondelete="CASCADE"),
        nullable=False,
    )

    participant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("participants.id", ondelete="CASCADE"),
        nullable=False,
    )

    exam_day_id = Column(
        UUID(as_uuid=True),
        ForeignKey("exam_days.id", ondelete="CASCADE"),
        nullable=False,
    )

    status = Column(
        Enum(AttemptStatus, name="attempt_status_enum"),
        nullable=False,
        default=AttemptStatus.NOT_STARTED,
    )

    special_unlocked = Column(Boolean, nullable=False, default=False)
    bonus_entered = Column(Boolean, nullable=False, default=False)

    started_at = Column(DateTime(timezone=True), nullable=True)
    allowed_duration_seconds = Column(Integer, nullable=False)

    submitted_at = Column(DateTime(timezone=True))
    total_time_seconds = Column(Integer)

    raw_score = Column(Numeric(10, 2), nullable=False, server_default="0")
    final_score = Column(Numeric(10, 2), nullable=False, server_default="0")

    # ⭐ IMMUTABLE FINALIZE SNAPSHOT (archive)
    golden_snapshot = Column(JSON, nullable=True)

    # ⭐ SEQUENCING SNAPSHOT (operational)
    shuffle_seed = Column(String, nullable=True)
    question_pool_ids = Column(JSONB, nullable=True)

    scoring_version = Column(Integer, nullable=False, default=1)

    hints_used_count = Column(Integer, nullable=False, default=0)
    attendance_flag = Column(Boolean, nullable=False, default=False)

    # ⭐ idempotency guard
    progress_applied = Column(Boolean, nullable=False, default=False)

    start_ip = Column(String)
    start_user_agent = Column(String)
    last_ip = Column(String)
    last_user_agent = Column(String)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    current_index = Column(Integer, nullable=False, default=0)
    last_resumed_at = Column(DateTime(timezone=True), nullable=True)

    participant = relationship("Participant", backref="attempts")