import firebase_admin
from firebase_admin import credentials, auth
from pathlib import Path
import os
import logging

from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

logger = logging.getLogger(__name__)

FIREBASE_APP = None
FIREBASE_ENABLED = True

ENV = os.getenv("ENVIRONMENT", "dev")


# -----------------------------
# 🔥 INITIALIZE FIREBASE
# -----------------------------
def initialize_firebase():
    global FIREBASE_APP, FIREBASE_ENABLED

    if FIREBASE_APP:
        return FIREBASE_APP

    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT")

    print("\n🔥 [FIREBASE INIT]")
    print("🔥 ENVIRONMENT:", ENV)
    print("🔥 SERVICE ACCOUNT PATH:", service_account_path)

    if ENV == "dev":
        FIREBASE_ENABLED = False
        logger.warning("🔥 DEV MODE: Firebase disabled explicitly")
        return None

    if ENV == "production":
        if not service_account_path:
            raise Exception("🔥 Firebase must be configured in production")

        service_account_path = Path(service_account_path)

        if not service_account_path.exists():
            raise Exception(
                f"🔥 Firebase service account missing at {service_account_path}"
            )

        cred = credentials.Certificate(service_account_path)
        FIREBASE_APP = firebase_admin.initialize_app(cred)

        print("🔥 FIREBASE PROJECT ID:", FIREBASE_APP.project_id)

        logger.info("🔥 Firebase Admin SDK initialized (PRODUCTION)")
        return FIREBASE_APP

    raise Exception(f"Invalid ENVIRONMENT value: {ENV}")


# -----------------------------
# 🔥 VERIFY FIREBASE TOKEN
# -----------------------------
def verify_firebase_token(id_token: str):
    initialize_firebase()

    # -----------------------------
    # 🔥 DEV MODE
    # -----------------------------
  #  if ENV == "dev":
   #     logger.warning("🔥 DEV MODE: Returning mock Firebase user")
    #    return {
     #       "uid": "dev-user",
      #      "email": "test@example.com",
       #     "name": "Dev User",
       # }

    if ENV == "dev":
        logger.warning(f"🔥 DEV MODE: Mock user for token = {id_token}")

    # ✅ Extract index from token (dev-user-101 → 101)
    try:
        if id_token.startswith("dev-user-"):
            index = int(id_token.split("-")[-1])
        else:
            index = 1
    except:
        index = 1

    return {
        "uid": id_token,
        "email": f"loadtest_user_{index}@test.com",  # ✅ MATCH DB
        "name": f"Load Test User {index}",
    }



    # -----------------------------
    # 🔒 PRODUCTION VERIFICATION
    # -----------------------------
    try:
        print("\n🟠 Verifying Firebase token...")

        # 🕒 SERVER TIME
        server_time = datetime.now(timezone.utc)
        print("🕒 SERVER TIME (UTC):", server_time)

        # 🔥 VERIFY TOKEN (STRICT)
        decoded_token = auth.verify_id_token(id_token, clock_skew_seconds=5)

        if not decoded_token:
            raise Exception("Empty decoded token")

        if "uid" not in decoded_token or "email" not in decoded_token:
            raise Exception("Invalid Firebase token payload")

        # -----------------------------
        # 🧾 TOKEN TIME DEBUG
        # -----------------------------
        def ts(ts_value):
            if not ts_value:
                return None
            return datetime.fromtimestamp(ts_value, tz=timezone.utc)

        print("🧾 TOKEN iat:", decoded_token.get("iat"))
        print("🧾 TOKEN nbf:", decoded_token.get("nbf"))
        print("🧾 TOKEN exp:", decoded_token.get("exp"))

        print("🧾 iat (UTC):", ts(decoded_token.get("iat")))
        print("🧾 nbf (UTC):", ts(decoded_token.get("nbf")))
        print("🧾 exp (UTC):", ts(decoded_token.get("exp")))

        print("🟢 Firebase token verified")
        print("🟢 Token audience (aud):", decoded_token.get("aud"))
        print("🟢 Token issuer (iss):", decoded_token.get("iss"))

        logger.info("✅ Firebase token verified successfully")

        return decoded_token

    except Exception as e:
        print("\n🔴 Firebase verification ERROR:", str(e))
        logger.error(f"🔥 Firebase verification error: {repr(e)}")

        # 🔥 propagate exact error
        raise Exception(str(e))