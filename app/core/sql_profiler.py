"""
ERI Assessment Engine
---------------------

Minimal SQLAlchemy profiler.

Responsibilities

- Count SQL statements
- Measure cumulative SQL execution time

Nothing else.

No SQL logging.
No parameter capture.
No EXPLAIN.
No query analysis.

Designed for production qualification only.
"""

from time import perf_counter

from sqlalchemy import event

from app.db.session import engine
from app.core.request_metrics import get_metrics


@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(
    conn,
    cursor,
    statement,
    parameters,
    context,
    executemany,
):
    """
    Record query start time.
    """

    context._eri_profiler_query_start = perf_counter()


@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(
    conn,
    cursor,
    statement,
    parameters,
    context,
    executemany,
):
    """
    Record query duration.

    Adds elapsed SQL execution time to the
    current request metrics.
    """

    metrics = get_metrics()

    if metrics is None:
        return

    start = getattr(
        context,
        "_eri_profiler_query_start",
        None,
    )

    if start is None:
        return

    metrics.db_time += perf_counter() - start
    metrics.query_count += 1

    try:
        del context._eri_profiler_query_start
    except AttributeError:
        pass


@event.listens_for(engine, "handle_error")
def handle_error(exception_context):
    """
    Cleanup timing state if SQLAlchemy
    raises an exception before a query
    completes.
    """

    execution_context = exception_context.execution_context

    if execution_context is None:
        return

    try:
        del execution_context._eri_profiler_query_start
    except AttributeError:
        pass