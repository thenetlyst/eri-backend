import uuid

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.sql import func

from app.db.base import Base
from sqlalchemy.dialects.postgresql import JSONB

difficulty_enum = ENUM(
    "EASY",
    "MEDIUM",
    "HARD",
    name="difficulty_enum",
    create_type=False,
)


class Question(Base):
    __tablename__ = "questions"

    __table_args__ = (
        UniqueConstraint(
            "exam_day_id",
            "question_order",
            name="uq_examday_order",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    challenge_id = Column(
        UUID(as_uuid=True),
        ForeignKey("challenges.id", ondelete="CASCADE"),
        nullable=False,
    )

    exam_day_id = Column(
        UUID(as_uuid=True),
        ForeignKey("exam_days.id", ondelete="CASCADE"),
        nullable=False,
    )

    question_order = Column(Integer, nullable=False)

    question_text = Column(String, nullable=False)

    option_a = Column(String, nullable=False)
    option_b = Column(String, nullable=False)
    option_c = Column(String, nullable=False)
    option_d = Column(String, nullable=False)

    correct_option = Column(String(1), nullable=False)

    weight = Column(Numeric(8, 2), nullable=False)

    difficulty = Column(difficulty_enum, nullable=False)

    allocated_time_seconds = Column(Integer, nullable=False)

    hint_text = Column(String)

    hint_penalty_percentage = Column(Numeric(5, 2), nullable=False)

    is_special = Column(Boolean, nullable=False)
    content_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
