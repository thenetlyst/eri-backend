"""
ERI Assessment Engine
---------------------

Per-request profiling state.

This module intentionally stores ONLY lightweight timing metrics.

It contains:
- no logging
- no SQL inspection
- no business logic
- no external dependencies

The metrics are request-local using ContextVar, making them safe for:

- FastAPI
- asyncio
- concurrent workers
"""

from contextvars import ContextVar
from dataclasses import dataclass
from time import perf_counter
from typing import Optional


@dataclass
class RequestMetrics:
    """
    Lightweight metrics collected during a single request.
    """

    # Request lifecycle
    request_start: float

    # Database metrics
    db_time: float = 0.0
    query_count: int = 0

    # Future-proof (currently unused)
    commit_time: float = 0.0


# Request-local storage
_request_metrics: ContextVar[Optional[RequestMetrics]] = ContextVar(
    "request_metrics",
    default=None,
)


def start_request() -> RequestMetrics:
    """
    Initialize metrics for the current request.
    """
    metrics = RequestMetrics(
        request_start=perf_counter()
    )

    _request_metrics.set(metrics)

    return metrics


def get_metrics() -> Optional[RequestMetrics]:
    """
    Returns metrics for the current request.

    Returns None if profiling is not active.
    """
    return _request_metrics.get()


def clear_request() -> None:
    """
    Clears request-local metrics.

    Prevents accidental leakage between requests.
    """
    _request_metrics.set(None)