from contextvars import ContextVar
from time import perf_counter

_request_id: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)

_request_start: ContextVar[float | None] = ContextVar(
    "request_start",
    default=None,
)


def start_request_context(request_id: str):
    _request_id.set(request_id)
    _request_start.set(perf_counter())


def get_request_id():
    return _request_id.get()


def elapsed_ms():
    start = _request_start.get()

    if start is None:
        return None

    return round((perf_counter() - start) * 1000, 3)