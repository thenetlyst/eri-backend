# app/middleware/request_timeline.py

import logging
from time import perf_counter
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.request_context import start_request_context


logger = logging.getLogger(__name__)


class RequestTimelineMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(id(request))


        start = perf_counter()
        start_request_context(request_id)

        logger.info(
            "REQUEST_ENTER",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
            },
        )

        try:
            response = await call_next(request)
        finally:
            total_ms = (perf_counter() - start) * 1000

            logger.info(
                "REQUEST_EXIT",
                extra={
                    "request_id": request_id,
                    "total_ms": round(total_ms, 3),
                },
            )

        return response