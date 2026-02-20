from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Dev Auth"])


class DevLoginRequest(BaseModel):
    email: str


@router.post("/dev-login")
def dev_login(payload: DevLoginRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == payload.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ⭐ CRITICAL — token = real user UUID
    return {
        "access_token": str(user.id),
        "token_type": "bearer"
    }