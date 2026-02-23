from sqlalchemy import Column, String, DateTime, ForeignKey, BigInteger, func
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class AttemptEvent(Base):
    __tablename__ = "attempt_events"

    # ✅ MATCHES DB (bigint autoincrement)
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    attempt_id = Column(UUID(as_uuid=True), ForeignKey("attempts.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), nullable=True)

    event_type = Column(String, nullable=False)

    client_ts = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)