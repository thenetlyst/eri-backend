import uuid

from sqlalchemy import (
    Column,
    ForeignKey,
    DateTime,
    Boolean,
    Numeric,
    String,
    UniqueConstraint,
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

    selected_option = Column(String(1), nullable=False)

    is_correct = Column(Boolean, nullable=False)

    hint_used = Column(Boolean, nullable=False, default=False)

    hint_used_at = Column(DateTime(timezone=True))

    answered_at = Column(DateTime(timezone=True), nullable=False)

    raw_score = Column(Numeric(10, 2), nullable=False)

    effective_score = Column(Numeric(10, 2), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
