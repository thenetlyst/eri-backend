from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session


from app.core.config import settings


from app.api.deps import get_db
from app.services.progress_rebuild_service import (
    rebuild_participant_progress,
    rebuild_challenge_progress,
)

router = APIRouter(tags=["Admin Rebuild"])


# -------------------------------------------------
# ADMIN KEY GUARD
# -------------------------------------------------
def require_admin_key(x_admin_key: str = Header(None)):
#    if x_admin_key != "ERI_ADMIN_REBUILD":
    if x_admin_key != settings.RANKING_ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Admin access required")


# -------------------------------------------------
# SINGLE PARTICIPANT REBUILD
# -------------------------------------------------
@router.post("/rebuild-progress/{participant_id}/{challenge_id}")
def rebuild_progress(
    participant_id: str,
    challenge_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key),
):
    progress = rebuild_participant_progress(db, participant_id, challenge_id)
    return {
        "status": "rebuilt_single",
        "attendance": progress.attendance_count,
    }


# -------------------------------------------------
# FULL CHALLENGE REBUILD
# -------------------------------------------------
@router.post("/rebuild-progress-challenge/{challenge_id}")
def rebuild_progress_challenge_endpoint(
    challenge_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key),
):
    result = rebuild_challenge_progress(db, challenge_id)
    return result