import logging

from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_db
from app.models.registration_application import RegistrationApplication
from app.models.user import User
from app.models.participant import Participant
from app.core.firebase import verify_firebase_token
from app.core.exceptions import ForbiddenException, ConflictException

router = APIRouter(tags=["Authentication"])

logger = logging.getLogger(__name__)

# 🔐 Proper Swagger-integrated security
security = HTTPBearer()


@router.post("/enroll")
def enroll(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Enroll a registered user into a challenge.
    Requires valid Firebase ID token in Authorization header.
    """

    # -------------------------------------------------
    # 1️⃣ Extract Firebase ID Token
    # -------------------------------------------------
    if not credentials:
        raise ForbiddenException("Missing Authorization header")

    id_token = credentials.credentials

    # -------------------------------------------------
    # 2️⃣ Verify Firebase Token
    # -------------------------------------------------
    decoded_token = verify_firebase_token(id_token)

    if not decoded_token:
        raise ForbiddenException("Invalid Firebase token")

    email = decoded_token.get("email")
    firebase_uid = decoded_token.get("uid")

    if not email or not firebase_uid:
        raise ForbiddenException("Invalid Firebase token payload")

    email = email.lower()

    # -------------------------------------------------
    # 3️⃣ Validate Registration Exists
    # -------------------------------------------------
    registration = (
        db.query(RegistrationApplication)
        .filter(RegistrationApplication.email == email)
        .first()
    )

    if not registration:
        raise ForbiddenException("Email not registered for this challenge")

    # -------------------------------------------------
    # 4️⃣ Create or Fetch User
    # -------------------------------------------------
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # First login → create user
        user = User(
            email=email,
            firebase_uid=firebase_uid,
        )
        db.add(user)
        db.flush()
    else:
        # Ensure UID consistency
        if user.firebase_uid != firebase_uid:
            raise ForbiddenException("Firebase UID mismatch")

    # -------------------------------------------------
    # 5️⃣ Create or Fetch Participant
    # -------------------------------------------------
    participant = (
        db.query(Participant)
        .filter(
            Participant.user_id == user.id,
            Participant.challenge_id == registration.challenge_id
        )
        .first()
    )

    if not participant:
        participant = Participant(
            user_id=user.id,
            challenge_id=registration.challenge_id,
            participant_code=registration.participant_code,
            state=registration.state,
            college=registration.college,
        )
        db.add(participant)

    # -------------------------------------------------
    # 6️⃣ Mark Registration Enrolled
    # -------------------------------------------------
    registration.enrolled = True

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictException("Enrollment conflict")

    logger.info(
        "Enrollment successful",
        extra={"email": email}
    )

    return {
        "participant_id": str(participant.id),
        "participant_code": participant.participant_code,
        "challenge_id": str(participant.challenge_id),
    }
