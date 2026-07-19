"""
ERI Request Trace
=================

Lightweight request profiler used throughout the ERI backend.

Goals
-----
- Very low overhead
- Production safe
- Automatically feeds RequestProfilerMiddleware
- Can be used anywhere in the request lifecycle

Example
-------

trace = RequestTrace(request)

with trace.measure("auth"):
    ...

with trace.measure("participant_lookup"):
    ...

trace.add_metric("cache_hit", True)

logger.info(trace.summary())
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any, Dict, Optional


class RequestTrace:

    def __init__(self, request=None):

        self.request = request

        self._request_start = time.perf_counter()

        self._phases: Dict[str, Any] = {}

    @contextmanager
    def measure(self, phase: str):

        start = time.perf_counter()

        try:
            yield

        finally:

            elapsed = (
                time.perf_counter() - start
            ) * 1000

            elapsed = round(elapsed, 3)

            self._phases[phase] = elapsed

            # Automatically expose phase timings
            # to the request profiler middleware.
            if (
                self.request is not None
                and hasattr(self.request.state, "profile")
            ):
                self.request.state.profile[phase] = elapsed

    def add_metric(
        self,
        name: str,
        value: Any,
    ) -> None:
        """
        Store any custom metric.

        Examples
        --------
        trace.add_metric("cache_hit", True)
        trace.add_metric("sql_queries", 6)
        trace.add_metric("connection_wait_ms", 12.4)
        """

        self._phases[name] = value

        if (
            self.request is not None
            and hasattr(self.request.state, "profile")
        ):
            self.request.state.profile[name] = value

    @property
    def total_ms(self) -> float:

        return round(
            (
                time.perf_counter()
                - self._request_start
            ) * 1000,
            3,
        )

    @property
    def phases(self) -> Dict[str, Any]:

        return dict(self._phases)

    def summary(self) -> Dict[str, Any]:

        return {
            "total_ms": self.total_ms,
            "phases": self.phases,
        }

    def reset(self) -> None:

        self._request_start = time.perf_counter()

        self._phases.clear()

    def mark_endpoint_start(self) -> None:

        if self.request is not None:
            self.request.state.endpoint_start = time.perf_counter()

    def mark_endpoint_end(self) -> None:

        if self.request is not None:
            self.request.state.endpoint_end = time.perf_counter()