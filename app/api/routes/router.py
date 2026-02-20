from fastapi import APIRouter

# Core routes
from app.api.routes.auth import router as auth_router
from app.api.routes.dev_auth import router as dev_auth_router
from app.api.routes.challenge import router as challenge_router
from app.api.routes.participant import router as participant_router
from app.api.routes.exam_day import router as exam_day_router
from app.api.routes.attempt import router as attempt_router
from app.api.routes.attempt_snapshot import router as attempt_snapshot_router

# Question routes
from app.api.routes.question import router as question_router
from app.api.routes.question_admin import router as question_admin_router

# Ranking
from app.api.routes.ranking import router as ranking_router


api_router = APIRouter()

# -----------------------------
# Auth
# -----------------------------
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(dev_auth_router, prefix="/auth", tags=["Dev Auth"])

# -----------------------------
# Core entities
# -----------------------------
api_router.include_router(challenge_router, prefix="/challenges", tags=["Challenges"])
api_router.include_router(participant_router, prefix="/participants", tags=["Participants"])
api_router.include_router(exam_day_router, prefix="/exam-days", tags=["Exam Days"])

# -----------------------------
# Attempts
# -----------------------------
api_router.include_router(attempt_router, prefix="/attempts", tags=["Attempts"])
api_router.include_router(attempt_snapshot_router, prefix="/attempts", tags=["Attempt Snapshot"])

# -----------------------------
# Questions
# -----------------------------
api_router.include_router(question_router, prefix="/questions", tags=["Questions"])
api_router.include_router(
    question_admin_router,
    prefix="/questions/admin",
    tags=["Question Admin"],
)

# -----------------------------
# Ranking
# -----------------------------
api_router.include_router(ranking_router, prefix="/ranking", tags=["Ranking"])