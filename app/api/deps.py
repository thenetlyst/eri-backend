from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.user import User

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
# AUTH Dependency (DEV BYPASS)
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

    # ⭐ DEV TOKEN BYPASS
    if token == "dev-token":
        user = db.query(User).first()

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Create a user row first",
            )

        return user

    raise HTTPException(
        status_code=401,
        detail="Invalid token",
    )