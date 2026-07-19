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
from app.core.request_profiler import RequestProfilerMiddleware
from app.core.request_context import start_request_context

from app.core.runtime_metrics import runtime_metrics

from app.db.session import (
    engine,
    pool_metrics,
    active_connections,
    _pool_lock,
)


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

app.add_middleware(RequestProfilerMiddleware)

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

    runtime_metrics.begin_request()

    try:
        # ------------------------------------------------------
        # Measure the entire FastAPI/Starlette request pipeline
        # ------------------------------------------------------
        before_call_next = perf_counter()

        response = await call_next(request)

        after_call_next = perf_counter()

        call_next_ms = round(
            (after_call_next - before_call_next) * 1000,
            3,
        )

        # Start measuring header processing
        before_headers = perf_counter()

    except Exception:
        logger.exception(
            "Unhandled exception during request",
            extra={"request_id": request_id},
        )

        runtime_metrics.fail_request()

        if ENABLE_PROFILING:
            clear_request()

        raise

    # ------------------------------------------------------
    # Total request time
    # ------------------------------------------------------
    total_ms = round(
        (perf_counter() - request_start) * 1000,
        3,
    )

    runtime_metrics.finish_request(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=total_ms,
    )

    # ------------------------------------------------------
    # SQL profiling
    # ------------------------------------------------------
    if ENABLE_PROFILING:
        metrics = get_metrics()

        db_ms = round(metrics.db_time * 1000, 2) if metrics else 0.0
        queries = metrics.query_count if metrics else 0

        response.headers["X-DB-Time"] = str(db_ms)
        response.headers["X-DB-Queries"] = str(queries)

    else:
        logger.info(
            f"⚡ {request.method} {request.url.path} | {total_ms} ms",
            extra={"request_id": request_id},
        )

    # ------------------------------------------------------
    # Standard response headers
    # ------------------------------------------------------
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Request-Time"] = str(total_ms)

    response.headers["X-Worker-PID"] = str(runtime_metrics.pid)
    response.headers["X-Backend"] = runtime_metrics.hostname

    # ------------------------------------------------------
    # Measure header processing
    # ------------------------------------------------------
    after_headers = perf_counter()

    header_ms = round(
        (after_headers - before_headers) * 1000,
        3,
    )

    unexplained_ms = round(
        total_ms - call_next_ms - header_ms,
        3,
    )

    # ------------------------------------------------------
    # Final diagnostics log
    # ------------------------------------------------------
    if ENABLE_PROFILING:
        logger.info(
            "request_complete",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": total_ms,
                "call_next_ms": call_next_ms,
                "header_ms": header_ms,
                "unexplained_ms": unexplained_ms,
                "db_ms": db_ms,
                "queries": queries,
            },
        )

        clear_request()

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


# ==========================================================
# Runtime Diagnostics
# ==========================================================

@app.get("/pq/runtime")
def runtime_info():
    """
    Runtime information for this backend worker.
    """
    return runtime_metrics.runtime_snapshot()


@app.get("/pq/metrics")
def metrics():
    """
    Request metrics.
    """

    snapshot = runtime_metrics.runtime_snapshot()

    return {
        "active_requests": snapshot["active_requests"],
        "completed_requests": snapshot["completed_requests"],
        "failed_requests": snapshot["failed_requests"],
        "total_requests": snapshot["total_requests"],
        "average_latency_ms": snapshot["average_latency_ms"],
        "max_latency_ms": snapshot["max_latency_ms"],
    }


@app.get("/pq/requests")
def recent_requests():
    """
    Recent requests handled by this worker.
    """

    history = runtime_metrics.request_history()

    return {
        "count": len(history),
        "requests": history,
    }


@app.get("/pq/pool")
def pool():

    return {
        "status": engine.pool.status(),

        "checked_out": pool_metrics["checked_out"],
        "peak_checked_out": pool_metrics["peak_checked_out"],

        "total_checkouts": pool_metrics["total_checkouts"],
        "total_checkins": pool_metrics["total_checkins"],
    }


@app.get("/pq/connections")
def connections():

    now = time.time()

    with _pool_lock:

        snapshot = []

        for conn_id, info in active_connections.items():

            snapshot.append(
                {
                    "connection_id": conn_id,
                    "worker_pid": info["pid"],
                    "thread_id": info["thread"],
                    "checked_out_seconds": round(
                        now - info["checkout_time"],
                        3,
                    ),
                    "checkout_timestamp": info["checkout_timestamp"],
                    "stack": info["stack"],
                }
            )

    snapshot.sort(
        key=lambda x: x["checked_out_seconds"],
        reverse=True,
    )

    return {
        "worker_pid": runtime_metrics.pid,
        "hostname": runtime_metrics.hostname,

        "checked_out": len(snapshot),

        "connections": snapshot,
    }