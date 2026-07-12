from fastapi import APIRouter, HTTPException
import os

router = APIRouter()

ENV = os.getenv("ENVIRONMENT", "dev")


@router.post("/dev-login")
def dev_login():
    """
    Temporary compatibility endpoint for frontend.
    Disabled in production.
    """

    if ENV != "dev":
        raise HTTPException(status_code=403, detail="Disabled in production")

    return {
        "access_token": "anything",
        "token_type": "bearer"
    }