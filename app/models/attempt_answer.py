import uuid

from sqlalchemy import (
    Column,
    ForeignKey,
    DateTime,
    Boolean,
    Numeric,
    String,
    UniqueConstraint,
    Integer,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class AttemptAnswer(Base):
    __tablename__ = "attempt_answers"

    __table_args__ = (
        UniqueConstraint(
            "attempt_id",
            "question_id",
            name="uq_attempt_answer_question"
        ),
        Index(
            "idx_attemptanswer_attempt",
            "attempt_id",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    attempt_id = Column(
        UUID(as_uuid=True),
        ForeignKey("attempts.id", ondelete="CASCADE"),
        nullable=False,
    )

    question_id = Column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # -----------------------------
    # CORE ANSWER DATA
    # -----------------------------
    selected_option = Column(String(1), nullable=False)

    is_correct = Column(
        Boolean,
        nullable=False,
        default=False,   # ✅ SAFE DEFAULT
    )

    answered_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    # -----------------------------
    # SCORING (FROZEN SNAPSHOT)
    # -----------------------------
    raw_score = Column(
        Numeric(10, 2),
        nullable=False,
        default=0,   # ✅ SAFE DEFAULT
    )

    effective_score = Column(
        Numeric(10, 2),
        nullable=False,
        default=0,   # ✅ SAFE DEFAULT
    )

    is_special = Column(
        Boolean,
        nullable=False,
        default=False,   # ✅ SAFE DEFAULT
    )

    weight_used = Column(
        Numeric(10, 2),
        nullable=False,
        default=0,   # ✅ SAFE DEFAULT
    )

    # -----------------------------
    # HINT TRACKING
    # -----------------------------
    hint_used = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    hint_used_at = Column(DateTime(timezone=True))

    first_hint_opened_at = Column(DateTime(timezone=True))

    answer_change_count = Column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    time_to_first_hint_seconds = Column(Integer)

    # -----------------------------
    # NAVIGATION TRACKING
    # -----------------------------
    visited_at = Column(DateTime(timezone=True))
    last_viewed_at = Column(DateTime(timezone=True))

    marked_for_review = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    # -----------------------------
    # AUDIT / SYSTEM
    # -----------------------------
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )