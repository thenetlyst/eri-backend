from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Dev Auth"])

@router.post("/dev-login")
def dev_login():
    return {
        "access_token": "dev-token",
        "token_type": "bearer"
    }
