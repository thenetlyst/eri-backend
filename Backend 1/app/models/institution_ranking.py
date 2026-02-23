import uuid

from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class InstitutionRanking(Base):
    __tablename__ = "institution_rankings"

    __table_args__ = (
        UniqueConstraint("challenge_id", "college", name="uq_challenge_college"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    challenge_id = Column(
        UUID(as_uuid=True),
        ForeignKey("challenges.id", ondelete="CASCADE"),
        nullable=False,
    )

    college = Column(String, nullable=False)
    state = Column(String, nullable=False)

    participant_count = Column(Integer, nullable=False)

    avg_percentile = Column(Numeric(6, 3))
    completion_rate = Column(Numeric(6, 3))
    participation_index = Column(Numeric(8, 4))

    institutional_index = Column(Numeric(10, 4))

    global_institution_rank = Column(Integer)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
