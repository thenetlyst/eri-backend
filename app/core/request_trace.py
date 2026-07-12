"""
ERI Request Trace
=================

Lightweight phase profiler for request lifecycle analysis.

Purpose:
- Measure where request time is spent.
- Extremely low overhead.
- No dependencies.
- Safe for production profiling.

Example:

    trace = RequestTrace()

    with trace.measure("auth"):
        ...

    with trace.measure("lookup"):
        ...

    logger.info(trace.summary())

"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Dict


class RequestTrace:
    def __init__(self):
        self._request_start = time.perf_counter()
        self._phases: Dict[str, float] = {}

    @contextmanager
    def measure(self, phase: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            self._phases[phase] = round(elapsed, 3)

    @property
    def total_ms(self) -> float:
        return round(
            (time.perf_counter() - self._request_start) * 1000,
            3,
        )

    @property
    def phases(self) -> Dict[str, float]:
        return dict(self._phases)

    def summary(self) -> Dict:
        return {
            "total_ms": self.total_ms,
            "phases": self.phases,
        }

    def reset(self):
        self._request_start = time.perf_counter()
        self._phases.clear()