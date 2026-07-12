import os
#print("🔥 RUNNING FROM:", os.getcwd())

import uuid
import logging
import threading
import time
from time import perf_counter
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException as FastAPIHTTPException

from app.api.routes.router import api_router
from app.core.logging_config import setup_logging
from app.core.firebase import initialize_firebase
from app.core.api_error import ApiError
from app.core.error_codes import ErrorCode
from app.core.config import settings
from app.core.request_metrics import (
    start_request,
    get_metrics,
    clear_request,
)
from app.core.request_context import start_request_context
# ----------------------------------------------------------
# ENV FLAGS
# ----------------------------------------------------------

ENABLE_API_STATS = os.getenv("ENABLE_API_STATS", "false").lower() == "true"
ENABLE_PROFILING = os.getenv("ENABLE_PROFILING", "false").lower() == "true"

# ----------------------------------------------------------
# Logging
# ----------------------------------------------------------

setup_logging()
logger = logging.getLogger(__name__)

if ENABLE_PROFILING:
    import app.core.sql_profiler  # Registers SQLAlchemy listeners

# ----------------------------------------------------------
# API STATS
# ----------------------------------------------------------

endpoint_counts = defaultdict(int)

def print_api_stats():
    while True:
        time.sleep(10)
        print("\n📊 ===== API STATS =====")
        for endpoint, count in endpoint_counts.items():
            print(f"{endpoint}: {count}")
        print("========================\n")

# ----------------------------------------------------------
# App
# ----------------------------------------------------------

app = FastAPI(title="ERI Assessment Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting ERI backend (stateless mode)")
    initialize_firebase()

    if ENABLE_API_STATS:
        logger.info("📊 API stats logger ENABLED")
        threading.Thread(target=print_api_stats, daemon=True).start()
    else:
        logger.info("📊 API stats logger DISABLED")

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_request_context(request_id)

    endpoint_counts[request.url.path] += 1

    if ENABLE_PROFILING:
        start_request()

    request_start = perf_counter()

    try:
        app_start = perf_counter()

        response = await call_next(request)

        app_ms = round(
            (perf_counter() - app_start) * 1000,
            3,
        )

    except Exception:
        logger.exception(
            "Unhandled exception during request",
            extra={"request_id": request_id},
        )
        if ENABLE_PROFILING:
            clear_request()
        raise

    total_ms = round(
        (perf_counter() - request_start) * 1000,
        3,
    )

    if ENABLE_PROFILING:
        metrics = get_metrics()
        db_ms = round(metrics.db_time * 1000, 2) if metrics else 0.0
        queries = metrics.query_count if metrics else 0

        logger.info(
            "request_complete",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": total_ms,
                "app_ms": app_ms,
                "middleware_overhead_ms": round(
                    total_ms - app_ms,
                    3,
                ),
                "db_ms": db_ms,
                "queries": queries,
            },
        )

        response.headers["X-DB-Time"] = str(db_ms)
        response.headers["X-DB-Queries"] = str(queries)
        clear_request()
    else:
        logger.info(
            f"⚡ {request.method} {request.url.path} | {total_ms} ms",
            extra={"request_id": request_id},
        )

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Request-Time"] = str(total_ms)
    return response

@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": {
                "code": ErrorCode.UNKNOWN_ERROR,
                "message": str(exc.detail),
                "meta": {},
            }
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server error")
    return JSONResponse(
        status_code=500,
        content={
            "detail": {
                "code": ErrorCode.INTERNAL_SERVER_ERROR,
                "message": "Internal server error",
                "meta": {},
            }
        },
    )

app.include_router(api_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}


import socket

@app.get("/pq/backend-stats")
def backend_stats():
    return {
        "hostname": socket.gethostname(),
        "pid": os.getpid(),
        "requests": dict(endpoint_counts),
        "total_requests": sum(endpoint_counts.values()),
    }