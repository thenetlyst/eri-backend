from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from app.models.attempt import Attempt, AttemptStatus
from app.models.user import User

from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
)

from app.services.attempt_service import finalize_attempt


def load_active_attempt(
    db: Session,
    attempt_id: str,
    current_user: User,
) -> tuple[Attempt, int]:
    """
    Returns a validated IN_PROGRESS attempt.

    Guarantees:
    - attempt exists
    - belongs to current user
    - attempt is active
    - timer has not expired
    - expired attempts are auto-finalized

    Returns:
        (attempt, remaining_time_seconds)
    """

    attempt = (
        db.query(Attempt)
        .filter(Attempt.id == attempt_id)
        .first()
    )

    if not attempt:
        raise NotFoundException("Attempt not found")

    if attempt.participant.user_id != current_user.id:
        raise ForbiddenException("Unauthorized access to attempt")

    if attempt.status == AttemptStatus.SUBMITTED:
        raise ForbiddenException("Attempt already completed")

    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise ForbiddenException("Attempt is not active")

    if attempt.started_at is None:
        raise ForbiddenException("Attempt not properly started")

    if attempt.allowed_duration_seconds is None:
        raise ForbiddenException("Attempt duration not configured")

    now = datetime.now(timezone.utc)

    expiry = (
        attempt.started_at +
        timedelta(seconds=attempt.allowed_duration_seconds)
    )

    if now > expiry:
        finalize_attempt(db, attempt)
        db.commit()
        raise ForbiddenException("Attempt time expired")

    remaining = int((expiry - now).total_seconds())

    return attempt, max(remaining, 0)