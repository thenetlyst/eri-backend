# app/middleware/request_timeline.py

import logging
from time import perf_counter
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.request_context import (
    start_request_context,
    get_request_id,
)

logger = logging.getLogger(__name__)


class RequestTimelineMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):

        request_id = request.headers.get("X-Request-ID")

        if not request_id:
            request_id = str(id(request))

        start_request_context(request_id)

        start = perf_counter()

        logger.info(
            "REQUEST_ENTER",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "t_ms": 0.0,
            },
        )

        try:

            response = await call_next(request)

            return response

        finally:

            total_ms = round(
                (perf_counter() - start) * 1000,
                3,
            )

            logger.info(
                "REQUEST_EXIT",
                extra={
                    "request_id": request_id,
                    "t_ms": total_ms,
                },
            )