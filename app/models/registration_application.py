import uuid
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class RegistrationApplication(Base):
    __tablename__ = "registration_applications"

    __table_args__ = (
        UniqueConstraint(
            "email",
            "challenge_id",
            name="uq_registration_email_challenge"
        ),
        UniqueConstraint(
            "participant_code",
            name="uq_registration_participant_code"
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    challenge_id = Column(
        UUID(as_uuid=True),
        ForeignKey("challenges.id", ondelete="CASCADE"),
        nullable=False,
    )

    email = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    state = Column(String, nullable=False)
    college = Column(String, nullable=False)
    graduation_year = Column(String, nullable=False)

    participant_code = Column(String, nullable=False, index=True)

    enrolled = Column(Boolean, nullable=False, default=False)

    welcome_email_sent_at = Column(DateTime(timezone=True))
    welcome_email_status = Column(String)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
