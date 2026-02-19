import firebase_admin
from firebase_admin import credentials, auth
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)

FIREBASE_APP = None


def initialize_firebase():
    """
    Initialize Firebase Admin SDK once.
    Safe for multiple calls.
    """
    global FIREBASE_APP

    if FIREBASE_APP:
        return FIREBASE_APP

    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT")

    if not service_account_path:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT env variable not set")

    service_account_path = Path(service_account_path)

    if not service_account_path.exists():
        raise RuntimeError(
            f"Firebase service account file not found at {service_account_path}"
        )

    cred = credentials.Certificate(service_account_path)

    FIREBASE_APP = firebase_admin.initialize_app(cred)

    logger.info("🔥 Firebase Admin SDK initialized successfully")

    return FIREBASE_APP


def verify_firebase_token(id_token: str):
    """
    Verify Firebase ID token.
    Returns decoded token dict if valid.
    Returns None if invalid.
    """
    try:
        initialize_firebase()

        decoded_token = auth.verify_id_token(id_token)

        logger.info("✅ Firebase token verified successfully")

        return decoded_token

    except Exception as e:
        logger.error(f"🔥 Firebase verification error: {repr(e)}")
        return None
