import uuid

from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class Ranking(Base):
    __tablename__ = "rankings"

    __table_args__ = (
        UniqueConstraint(
            "challenge_id",
            "participant_id",
            name="uq_challenge_participant_rank"
        ),

        # 🔥 Critical performance indexes
        Index(
            "idx_rankings_challenge_score",
            "challenge_id",
            "total_score"
        ),

        Index(
            "idx_rankings_challenge_global_rank",
            "challenge_id",
            "global_rank"
        ),
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

    total_score = Column(Numeric(10, 2), nullable=False)
    percentile = Column(Numeric(6, 3))

    global_rank = Column(Integer)
    state_rank = Column(Integer)
    institution_rank = Column(Integer)

    ranking_finalized = Column(Boolean, nullable=False, default=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
