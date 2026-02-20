import uuid
import time
import logging

from fastapi import FastAPI, Request
from app.api.routes.challenge import router as challenge_router
from app.api.routes.attempt import router as attempt_router
from app.api.routes.participant import router as participant_router
from app.api.routes.question import router as question_router
from app.core.logging_config import setup_logging
from app.api.routes.ranking import router as ranking_router
from app.api.routes.auth import router as auth_router
from app.core.firebase import initialize_firebase

#FRONT-END

from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.dev_auth import router as dev_auth_router



# ----------------------------------------------------------
# Initialize Logging
# ----------------------------------------------------------

setup_logging()
logger = logging.getLogger(__name__)


# ----------------------------------------------------------
# Create FastAPI App
# ----------------------------------------------------------

app = FastAPI(title="ERI Assessment Engine")

#FrontEnd

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev mode
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------------
# Startup Event
# ----------------------------------------------------------
app.include_router(dev_auth_router)

@app.on_event("startup")
def startup_event():
    initialize_firebase()


# ----------------------------------------------------------
# Request Logging Middleware
# ----------------------------------------------------------

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "Unhandled exception during request",
            extra={"request_id": request_id}
        )
        raise

    duration_ms = round((time.time() - start_time) * 1000, 2)

    logger.info(
        f"{request.method} {request.url.path} completed in {duration_ms}ms",
        extra={"request_id": request_id},
    )

    response.headers["X-Request-ID"] = request_id
    return response


# ----------------------------------------------------------
# Routers
# ----------------------------------------------------------

app.include_router(
    challenge_router,
    prefix="/challenges",
    tags=["Challenges"]
)

app.include_router(
    attempt_router,
    prefix="/attempts",
    tags=["Attempts"]
)

app.include_router(
    participant_router,
    prefix="/participants",
    tags=["Participants"]
)

app.include_router(question_router)
app.include_router(ranking_router)
app.include_router(auth_router)

# ----------------------------------------------------------
# Health Check
# ----------------------------------------------------------

@app.get("/health")
def health_check():
    return {"status": "ok"}
