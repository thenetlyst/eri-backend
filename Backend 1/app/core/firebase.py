import firebase_admin
from firebase_admin import credentials, auth
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)

FIREBASE_APP = None
FIREBASE_ENABLED = True


def initialize_firebase():
    """
    Initialize Firebase Admin SDK once.
    Safe for multiple calls.
    Runs in optional mode for local dev.
    """
    global FIREBASE_APP, FIREBASE_ENABLED

    if FIREBASE_APP:
        return FIREBASE_APP

    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT")

    # ⭐ DEV MODE — Firebase optional
    if not service_account_path:
        FIREBASE_ENABLED = False
        logger.warning("🔥 Firebase not configured — running without Firebase")
        return None

    service_account_path = Path(service_account_path)

    if not service_account_path.exists():
        FIREBASE_ENABLED = False
        logger.warning(
            f"🔥 Firebase service account missing at {service_account_path} — skipping"
        )
        return None

    cred = credentials.Certificate(service_account_path)

    FIREBASE_APP = firebase_admin.initialize_app(cred)

    logger.info("🔥 Firebase Admin SDK initialized successfully")

    return FIREBASE_APP


def verify_firebase_token(id_token: str):
    """
    Verify Firebase ID token.
    Returns decoded token dict if valid.
    Returns mock token if Firebase disabled (dev mode).
    """

    initialize_firebase()

    # ⭐ DEV MODE fallback
    if not FIREBASE_ENABLED:
        logger.warning("🔥 Firebase disabled — returning mock user")
        return {
            "uid": "dev-user",
            "email": "dev@eri.local",
            "name": "Dev User",
        }

    try:
        decoded_token = auth.verify_id_token(id_token)

        logger.info("✅ Firebase token verified successfully")

        return decoded_token

    except Exception as e:
        logger.error(f"🔥 Firebase verification error: {repr(e)}")
        return None