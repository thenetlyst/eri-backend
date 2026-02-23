import uuid

from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class Response(Base):
    __tablename__ = "responses"

    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question"),
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

    selected_option = Column(String(1))
    is_correct = Column(Boolean)
    hint_used = Column(Boolean, nullable=False, default=False)

    answered_at = Column(DateTime(timezone=True))
    time_taken_seconds = Column(Integer)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
