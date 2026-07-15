from __future__ import annotations

import os
import socket
import threading
import resource
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Deque, Dict, List


# ---------------------------------------------------------
# Request Record
# ---------------------------------------------------------

@dataclass(slots=True)
class RequestRecord:
    request_id: str
    method: str
    path: str
    status: int
    duration_ms: float
    timestamp: str


# ---------------------------------------------------------
# Runtime Metrics
# ---------------------------------------------------------

class RuntimeMetrics:
    """
    Lightweight process-local runtime metrics.

    One instance exists per Uvicorn worker.

    Responsibilities:
        • Worker identity
        • Request counters
        • Latency statistics
        • Recent request history

    No FastAPI dependencies.
    No SQLAlchemy dependencies.
    No database access.
    """

    def __init__(self, history_size: int = 500):

        self.hostname = socket.gethostname()
        self.pid = os.getpid()
        self.started_at = datetime.now(timezone.utc)

        self.active_requests = 0
        self.completed_requests = 0
        self.failed_requests = 0
        self.total_requests = 0

        self.total_latency_ms = 0.0
        self.max_latency_ms = 0.0

        self.recent_requests: Deque[RequestRecord] = deque(
            maxlen=history_size
        )

        self._lock = threading.Lock()

    # --------------------------------------------------

    def begin_request(self) -> None:
        with self._lock:
            self.active_requests += 1
            self.total_requests += 1

    # --------------------------------------------------

    def finish_request(
        self,
        *,
        request_id: str,
        method: str,
        path: str,
        status: int,
        duration_ms: float,
    ) -> None:

        record = RequestRecord(
            request_id=request_id,
            method=method,
            path=path,
            status=status,
            duration_ms=round(duration_ms, 3),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        with self._lock:

            if self.active_requests > 0:
                self.active_requests -= 1

            self.completed_requests += 1

            self.total_latency_ms += duration_ms

            if duration_ms > self.max_latency_ms:
                self.max_latency_ms = duration_ms

            self.recent_requests.append(record)

    # --------------------------------------------------

    def fail_request(self) -> None:
        with self._lock:

            if self.active_requests > 0:
                self.active_requests -= 1

            self.failed_requests += 1

    # --------------------------------------------------

    @property
    def average_latency_ms(self) -> float:

        if self.completed_requests == 0:
            return 0.0

        return round(
            self.total_latency_ms / self.completed_requests,
            3,
        )

    # --------------------------------------------------

    @staticmethod
    def _rss_mb() -> float:
        """
        Returns resident memory in MB.

        Linux reports ru_maxrss in KB.
        macOS reports bytes.
        """

        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        if os.name == "posix":
            return round(usage / 1024, 2)

        return round(usage / (1024 * 1024), 2)

    # --------------------------------------------------

    def runtime_snapshot(self) -> Dict:

        uptime = (
            datetime.now(timezone.utc) - self.started_at
        ).total_seconds()

        with self._lock:

            snapshot = {
                "hostname": self.hostname,
                "pid": self.pid,
                "started_at": self.started_at.isoformat(),
                "uptime_seconds": round(uptime, 1),

                "rss_mb": self._rss_mb(),
                "threads": threading.active_count(),

                "active_requests": self.active_requests,
                "completed_requests": self.completed_requests,
                "failed_requests": self.failed_requests,
                "total_requests": self.total_requests,

                "average_latency_ms": self.average_latency_ms,
                "max_latency_ms": round(self.max_latency_ms, 3),
            }

        return snapshot

    # --------------------------------------------------

    def request_history(self) -> List[Dict]:

        with self._lock:

            return [
                asdict(record)
                for record in reversed(self.recent_requests)
            ]

    # --------------------------------------------------

    def reset(self) -> None:
        """
        Useful for unit tests.
        Not intended for production use.
        """

        with self._lock:

            self.active_requests = 0
            self.completed_requests = 0
            self.failed_requests = 0
            self.total_requests = 0

            self.total_latency_ms = 0.0
            self.max_latency_ms = 0.0

            self.recent_requests.clear()


# ---------------------------------------------------------
# Singleton
# ---------------------------------------------------------

runtime_metrics = RuntimeMetrics()