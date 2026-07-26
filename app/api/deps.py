from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, get_db
from app.models.user import User
from app.core.firebase import verify_firebase_token
from app.core.errors import unauthorized
from app.core.error_codes import ErrorCode

import logging
from time import perf_counter

from app.core.request_context import (
    get_request_id,
    elapsed_ms,
)
from sqlalchemy.orm import make_transient

security = HTTPBearer()

logger = logging.getLogger(__name__)
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
        auth_start = perf_counter()

        logger.info(
            "AUTH_ENTER",
            extra={
                "request_id": get_request_id(),
                "elapsed_ms": elapsed_ms(),
            },
        )


        # -----------------------------
        # 1. Validate token presence
        # -----------------------------
        if not credentials or not credentials.credentials:
            unauthorized("Missing authentication token")
            return

        token = credentials.credentials

        logger.info(
            "TOKEN_PARSED",
            extra={"request_id": get_request_id(),"elapsed_ms": elapsed_ms(),},
        )

        # -----------------------------
        # 🔥 DEV MODE DIRECT HANDLING
        # -----------------------------
        if token.startswith("dev-user-"):
            try:
                index = int(token.split("-")[-1])
            except Exception:
                index = 1

            email = f"loadtest_user_{index}@test.com"

            lookup_start = perf_counter()

            logger.info(
                "USER_LOOKUP_BEGIN",
                extra={"request_id": get_request_id(),"elapsed_ms": elapsed_ms(),},
            )

            user = (
                db.query(User)
                    .filter(User.email == email)
                    .one_or_none()
            )

            logger.info(
                "USER_LOOKUP_END",
                extra={
                    "request_id": get_request_id(),
                    "elapsed_ms": elapsed_ms(),
                },
            )
 #       backend_pid = db.execute(text("SELECT pg_backend_pid()")).scalar_one()
            logger.info(
                "AUTH_QUERY_RETURNED",
                extra={
                    "request_id": get_request_id(),
                    "elapsed_ms": elapsed_ms(),
                },
            )

            lookup_ms = round(
                (perf_counter() - lookup_start) * 1000,
                3,
            )
        
            logger.info(
                "AUTH_LOOKUP",
                extra={
                    "request_id": get_request_id(),
                    "lookup_ms": lookup_ms,
                    "elapsed_ms": elapsed_ms(),
                },
            )
        
            if not user:
                print(f"❌ DEV USER NOT FOUND: {email}")
                unauthorized("User not found", code=ErrorCode.USER_NOT_FOUND)
                return

            duration_ms = round((perf_counter() - auth_start) * 1000, 3)

            logger.info(
                "auth_profile",
                extra={
                    "request_id": get_request_id(),
                    "elapsed_ms": elapsed_ms(),
                    "mode": "dev",
                    "duration_ms": duration_ms,
                },
            )

            logger.info(
                "SESSION_STATE",
                extra={
                    "request_id": get_request_id(),
                    "email": user.email,
                    "in_transaction": db.in_transaction(),
                    "is_active": db.is_active,
                    "elapsed_ms": elapsed_ms(),
                },
            )
            logger.info(
                "AUTH_RETURN_USER",
                extra={
                    "request_id": get_request_id(),
                    "user_id": str(user.id),
                    "email": user.email,
 #                  "pg_pid": backend_pid,
                    "elapsed_ms": elapsed_ms(),
                },
            )

            logger.info(
                "AUTH_EXIT",
                extra={"request_id": get_request_id(),"elapsed_ms": elapsed_ms(),},
            )
    
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

        duration_ms = round((perf_counter() - auth_start) * 1000, 3)

        logger.info(
            "auth_profile",
            extra={
                "request_id": get_request_id(),
                "elapsed_ms": elapsed_ms(),
                "mode": "firebase",
                "duration_ms": duration_ms,
            },
        )


        logger.info(
            "AUTH_RETURN_USER",
            extra={
                "request_id": get_request_id(),
                "elapsed_ms": elapsed_ms(),
            },
        )

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