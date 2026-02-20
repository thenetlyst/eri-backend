from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import uuid

from app.db.session import SessionLocal
from app.models.user import User   # ⚠️ note path

security = HTTPBearer()


# -----------------------------
# DB Dependency
# -----------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------
# AUTH Dependency (REAL UUID TOKEN)
# -----------------------------
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )

    token = credentials.credentials

    # ⭐ token IS user UUID now
    try:
        user_uuid = uuid.UUID(token)
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid token format",
        )

    user = db.query(User).filter(User.id == user_uuid).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    return user