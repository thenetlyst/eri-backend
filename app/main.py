
import logging

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



# ----------------------------------------------------------
# Logging
# ----------------------------------------------------------

setup_logging()
logger = logging.getLogger(__name__)

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
