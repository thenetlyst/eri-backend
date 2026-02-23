import uuid
import time
import logging
import asyncio

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.router import api_router
from app.core.logging_config import setup_logging
from app.core.firebase import initialize_firebase

# ✅ finalize loop import
from app.workers.finalize_worker import finalize_expired_attempts_loop


# ----------------------------------------------------------
# Logging
# ----------------------------------------------------------

setup_logging()
logger = logging.getLogger(__name__)


# ----------------------------------------------------------
# App
# ----------------------------------------------------------

app = FastAPI(title="ERI Assessment Engine")


# ----------------------------------------------------------
# CORS (dev mode)
# ----------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------------------------
# Startup
# ----------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    initialize_firebase()

    # ✅ Start background finalize loop
    asyncio.create_task(finalize_expired_attempts_loop())


# ----------------------------------------------------------
# Request logging middleware
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
# Attach ALL routers via api_router
# ----------------------------------------------------------

app.include_router(api_router)


# ----------------------------------------------------------
# Health
# ----------------------------------------------------------

@app.get("/health")
def health_check():
    return {"status": "ok"}