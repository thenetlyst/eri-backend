import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    firebase_uid = Column(String, unique=True, nullable=True, index=True)

    email = Column(String, nullable=False, unique=True, index=True)

    participant_code = Column(String, unique=True, nullable=True, index=True)

    # 🔥 ADD THIS LINE
    name = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )