import uuid
import enum

from sqlalchemy import Column, String, Enum, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class AccountStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DISQUALIFIED = "DISQUALIFIED"


class Participant(Base):
    __tablename__ = "participants"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "challenge_id",
            name="uq_user_challenge"
        ),
        UniqueConstraint(
            "participant_code",
            name="uq_participant_code"
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 🔑 identity link
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # 🔑 challenge enrollment
    challenge_id = Column(
        UUID(as_uuid=True),
        ForeignKey("challenges.id", ondelete="CASCADE"),
        nullable=False,
    )

    participant_code = Column(String, nullable=False)

    # 🔥 profile snapshot (this fixes your router errors)
    name = Column(String, nullable=False)
    college = Column(String, nullable=False)
    state = Column(String, nullable=False)
    graduation_year = Column(String, nullable=False)

    account_status = Column(
        Enum(AccountStatus, name="account_status_enum"),
        nullable=False,
        default=AccountStatus.ACTIVE,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())