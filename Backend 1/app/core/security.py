from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth

security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials):
    token = credentials.credentials

    # ✅ DEV BYPASS
    if token == "dev-token":
        return {"uid": "dev-user"}

    # ✅ REAL FIREBASE VERIFY (later)
    try:
        decoded = auth.verify_id_token(token)
        return decoded
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )