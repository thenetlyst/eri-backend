import os
from fastapi import APIRouter

# Core routes
from app.api.routes.challenge import router as challenge_router
from app.api.routes.participant import router as participant_router
from app.api.routes.exam_day import router as exam_day_router
from app.api.routes.attempt import router as attempt_router
from app.api.routes.attempt_snapshot import router as attempt_snapshot_router
from app.api.routes.attempt_reconstruct import router as attempt_reconstruct_router
from app.api.routes.admin_rebuild import router as admin_rebuild_router
from app.api.routes.attempt_events import router as attempt_events_router

# Question routes
from app.api.routes.question import router as question_router
from app.api.routes.question_admin import router as question_admin_router

# Ranking
from app.api.routes.ranking import router as ranking_router

# Dev auth
from app.api.routes.dev_auth import router as dev_auth_router
from app.api.routes import auth

# Admin CSV upload
from app.api.routes.admin_csv_upload import router as admin_csv_upload_router

# Exam Status
from app.api.routes.exam_status import router as exam_status_router

# ----------------------------------------------------------
# Environment
# ----------------------------------------------------------
ENV = os.getenv("ENVIRONMENT", "dev")

# ----------------------------------------------------------
# API Router
# ----------------------------------------------------------
api_router = APIRouter()

# ----------------------------------------------------------
# Auth
# ----------------------------------------------------------

# Register dev auth ONLY in development
if ENV == "dev":
    api_router.include_router(
        dev_auth_router,
        prefix="/auth",
        tags=["Auth"],
    )

# Firebase / Production authentication
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Auth"],
)

# ----------------------------------------------------------
# Core entities
# ----------------------------------------------------------
api_router.include_router(
    challenge_router,
    prefix="/challenges",
    tags=["Challenges"],
)

api_router.include_router(
    participant_router,
    prefix="/participants",
    tags=["Participants"],
)

api_router.include_router(
    exam_day_router,
    prefix="/exam-days",
    tags=["Exam Days"],
)

# ----------------------------------------------------------
# Attempts
# ----------------------------------------------------------
api_router.include_router(
    attempt_router,
    prefix="/attempts",
    tags=["Attempts"],
)

api_router.include_router(
    attempt_snapshot_router,
    prefix="/attempts",
    tags=["Attempt Snapshot"],
)

api_router.include_router(
    attempt_reconstruct_router,
    prefix="/attempts",
    tags=["Attempt Reconstruction"],
)

api_router.include_router(
    attempt_events_router,
    prefix="/attempts",
    tags=["Attempt Events"],
)

# ----------------------------------------------------------
# Questions
# ----------------------------------------------------------
api_router.include_router(
    question_router,
    prefix="/questions",
    tags=["Questions"],
)

api_router.include_router(
    question_admin_router,
    prefix="/questions/admin",
    tags=["Question Admin"],
)

# ----------------------------------------------------------
# Ranking
# ----------------------------------------------------------
api_router.include_router(
    ranking_router,
    prefix="/ranking",
    tags=["Ranking"],
)

# ----------------------------------------------------------
# Admin CSV Upload
# ----------------------------------------------------------
api_router.include_router(admin_csv_upload_router)

# ----------------------------------------------------------
# Exam Status
# ----------------------------------------------------------
api_router.include_router(exam_status_router)

# ----------------------------------------------------------
# Admin Rebuild
# ----------------------------------------------------------
api_router.include_router(
    admin_rebuild_router,
    prefix="/admin",
    tags=["Admin Rebuild"],
)