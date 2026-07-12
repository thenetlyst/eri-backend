from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(tags=["auth"])


@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Returns authenticated user info.
    Used by frontend after Firebase login.
    """

    return {
        "email": current_user.email,
        "participant_code": current_user.participant_code,
        "name": getattr(current_user, "name", None),
    }