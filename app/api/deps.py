from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, get_db
from app.models.user import User
from app.core.firebase import verify_firebase_token
from app.core.errors import unauthorized
from app.core.error_codes import ErrorCode

from sqlalchemy.orm import make_transient

security = HTTPBearer()

#from sqlalchemy import text

# -----------------------------
# AUTH Dependency (UNCHANGED LOGIC)
# -----------------------------
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    
    db: Session = SessionLocal()
    try:
        """
        Authentication flow:

        DEV MODE:
        - Direct mapping: dev-user-101 → loadtest_user_101@test.com

        PRODUCTION:
        - Firebase verification
        - UID + email lookup
        """

        # -----------------------------
        # 1. Validate token presence
        # -----------------------------
        if not credentials or not credentials.credentials:
            unauthorized("Missing authentication token")
            return

        token = credentials.credentials

        # -----------------------------
        # 🔥 DEV MODE DIRECT HANDLING
        # -----------------------------
        if token.startswith("dev-user-"):
            try:
                index = int(token.split("-")[-1])
            except Exception:
                index = 1

            email = f"loadtest_user_{index}@test.com"

            user = (
                db.query(User)
                    .filter(User.email == email)
                    .one_or_none()
            )

 #       backend_pid = db.execute(text("SELECT pg_backend_pid()")).scalar_one()
        
            if not user:
                unauthorized("User not found", code=ErrorCode.USER_NOT_FOUND)
                return
    
            # Force-load only fields that actually exist
            _ = (
                user.id,
                user.email,
                user.firebase_uid,
            )

            # Remove ORM identity/session association
            db.expunge(user)
            make_transient(user)

            return user
    
        # -----------------------------
        # 🔒 NORMAL FLOW (FIREBASE)
        # -----------------------------
        try:
            decoded_token = verify_firebase_token(token)
        except Exception:
            unauthorized("Token expired or invalid", code=ErrorCode.TOKEN_EXPIRED)
            return

        if not decoded_token:
            unauthorized("Invalid token")
            return

        # -----------------------------
        # Extract identity
        # -----------------------------
        firebase_uid = decoded_token.get("uid")
        email = decoded_token.get("email")

        if not firebase_uid or not email:
            unauthorized("Invalid token payload")
            return

        email = email.lower().strip()

        # -----------------------------
        # PRIMARY LOOKUP (UID)
        # -----------------------------
        user = db.query(User).filter(User.firebase_uid == firebase_uid).one_or_none()

        # -----------------------------
        # FALLBACK LOOKUP (EMAIL)
        # -----------------------------
        if not user:
            user = db.query(User).filter(User.email == email).one_or_none()

            if not user:
                unauthorized("User not found", code=ErrorCode.USER_NOT_FOUND)
                return

            # 🔥 First-time UID linking
            user.firebase_uid = firebase_uid
            db.commit()
            db.refresh(user)

        # -----------------------------
        # UID CONSISTENCY CHECK
        # -----------------------------
        elif user.firebase_uid != firebase_uid:
            unauthorized("Account mismatch detected", code=ErrorCode.UNAUTHORIZED)
            return

        # Force-load only fields that actually exist
        _ = (
            user.id,
            user.email,
            user.firebase_uid,
        )

        # Remove ORM identity/session association
        db.expunge(user)
        make_transient(user)

        return user
    finally:
        try:
            if db.in_transaction():
                db.rollback()
        finally:
            db.close()