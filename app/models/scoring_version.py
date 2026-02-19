from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class ScoringVersion(Base):
    __tablename__ = "scoring_versions"

    id = Column(Integer, primary_key=True)

    challenge_id = Column(
        UUID(as_uuid=True),
        ForeignKey("challenges.id", ondelete="CASCADE"),
        nullable=False,
    )

    description = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
