import json
import logging
import os
import threading
import uuid
import random
from datetime import datetime, timezone
from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger("request_profiler")

ENABLE_REQUEST_PROFILING = (
    os.getenv("ENABLE_REQUEST_PROFILING", "false").lower() == "true"
)


class RequestProfilerMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):

        if not ENABLE_REQUEST_PROFILING:
            return await call_next(request)

        # --------------------------------------------------
        # Request Context
        # --------------------------------------------------

        request.state.request_id = str(uuid.uuid4())

        request.state.request_start = perf_counter()

        request.state.endpoint_start = None
        request.state.endpoint_end = None

        request.state.profile = {
            "sql_queries": 0,
            "sql_total_ms": 0.0,
            "slowest_sql_ms": 0.0,
            "connection_wait_ms": 0.0,
            "pool_status": None,
        }

        response = None
        exception = None

        try:

            response = await call_next(request)

            return response

        except Exception:

            exception = True

            logger.exception(
                "Unhandled exception during request profiling"
            )

            raise

        finally:

            total_ms = (
                perf_counter()
                - request.state.request_start
            ) * 1000

            endpoint_ms = None
            middleware_before = None
            middleware_after = None

            if (
                request.state.endpoint_start is not None
                and request.state.endpoint_end is not None
            ):

                endpoint_ms = (
                    request.state.endpoint_end
                    - request.state.endpoint_start
                ) * 1000

                middleware_before = (
                    request.state.endpoint_start
                    - request.state.request_start
                ) * 1000

                middleware_after = (
                    perf_counter()
                    - request.state.endpoint_end
                ) * 1000

            payload = {

                "timestamp":
                    datetime.now(
                        timezone.utc
                    ).isoformat(),

                "profile_version":
                    1,

                "request_id":
                    request.state.request_id,

                "pid":
                    os.getpid(),

                "thread":
                    threading.get_ident(),

                "method":
                    request.method,

                "path":
                    request.url.path,

                "query":
                    request.url.query,

                "client":
                    request.client.host
                    if request.client
                    else None,

                "status":
                    response.status_code
                    if response
                    else 500,

                "total_ms":
                    round(total_ms, 2),

                "endpoint_ms":
                    round(endpoint_ms, 2)
                    if endpoint_ms is not None
                    else None,

                "middleware_before_endpoint_ms":
                    round(middleware_before, 2)
                    if middleware_before is not None
                    else None,

                "middleware_after_endpoint_ms":
                    round(middleware_after, 2)
                    if middleware_after is not None
                    else None,

                "exception":
                    exception,
            }

            payload.update(request.state.profile)

            if response is not None:
                response.headers[
                    "X-Request-ID"
                ] = request.state.request_id

            #
            # Log only 1 in every 1000 requests.
            # Keeps profiling overhead negligible while still
            # capturing representative slow requests.
            #
            if random.random() < 0.001:
                logger.error(
                    json.dumps(
                        payload,
                        default=str,
                    )
                )