from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

import logging
import time
from sqlalchemy import event
#import traceback
from datetime import datetime

logger = logging.getLogger(__name__)
from app.core.config import settings
#from sqlalchemy.pool import NullPool
from time import perf_counter


# --------------------------------------------------
# Pool Metrics
# --------------------------------------------------

from threading import Lock
import os
import threading
import uuid
from app.core.request_context import get_request_id


_pool_lock = Lock()

active_connections = {}


pool_metrics = {
    "checked_out": 0,
    "peak_checked_out": 0,
    "total_checkouts": 0,
    "total_checkins": 0,
    "longest_connection_ms": 0,
    "currently_active": 0,
}


# --------------------------------------------------
# Engine (UPDATED FOR LOAD)
# --------------------------------------------------

engine = create_engine(
    settings.DATABASE_URL,
    #echo=True, 
   # echo=False,
    #keep it as false only for load testing 


    # 🔥 Connection pool tuning (UPDATED)
    pool_size=50,          # ↑ base connections (was 20)
    max_overflow=50,      # ↑ burst capacity (was 40)
    pool_timeout=10,       # same
    pool_recycle=300,     # same
    pool_pre_ping=True,    # same
    
    echo=False,
    # ADD THIS (Importabt under load)
    connect_args={"connect_timeout": 5},
)

# --------------------------------------------------
# SQLAlchemy Pool Instrumentation
# --------------------------------------------------

@event.listens_for(engine, "checkout")
def checkout(dbapi_connection, connection_record, connection_proxy):
    connection_record.info["checkout_time"] = time.perf_counter()
    connection_uuid = str(uuid.uuid4())
    connection_record.info["connection_uuid"] = connection_uuid
    connection_record.info["first_query_time"] = None
    connection_record.info["last_query_time"] = None
    connection_record.info["last_query_sql"] = None
    connection_record.info["query_count"] = 0

#    connection_record.info["checkout_stack"] = "".join(
#        traceback.format_stack(limit=8)
#    )

    connection_record.info["checkout_stack"] = None

    connection_record.info["checkout_timestamp"] = datetime.utcnow().isoformat()

#    logger.info(
#        "[POOL] CHECKOUT %s",
#        connection_uuid,
#    )

    with _pool_lock:
        active_connections[connection_uuid] = {
            "pid": os.getpid(),
            "thread": threading.get_ident(),
            "checkout_time": time.time(),
            "checkout_timestamp": connection_record.info["checkout_timestamp"],
            "stack": connection_record.info["checkout_stack"],
        }

        pool_metrics["checked_out"] += 1
        pool_metrics["total_checkouts"] += 1

        if pool_metrics["checked_out"] > pool_metrics["peak_checked_out"]:
            pool_metrics["peak_checked_out"] = pool_metrics["checked_out"]


#        logger.info(
#            f"[POOL] CHECKOUT "
#            f"active={pool_metrics['checked_out']} "
#            f"peak={pool_metrics['peak_checked_out']} "
#            f"total={pool_metrics['total_checkouts']}"
#        )


@event.listens_for(engine, "checkin")
def checkin(dbapi_connection, connection_record):
    connection_uuid = connection_record.info.pop(
        "connection_uuid",
        None,
    )

    start = connection_record.info.pop("checkout_time", None)

    first_query = connection_record.info.pop(
        "first_query_time",
        None,
    )

    last_query = connection_record.info.pop(
        "last_query_time",
        None,
    )

    last_sql = connection_record.info.pop(
        "last_query_sql",
        None,
    )

    query_count = connection_record.info.pop(
        "query_count",
        0,
    )


    checkout_stack = connection_record.info.pop(
        "checkout_stack",
        "<no stack>",
    )


    with _pool_lock:
        if connection_uuid:
            active_connections.pop(connection_uuid, None)

        pool_metrics["checked_out"] -= 1
        pool_metrics["total_checkins"] += 1

#        logger.info(
#            f"[POOL] CHECKIN "
#            f"active={pool_metrics['checked_out']} "
#            f"returned={pool_metrics['total_checkins']}"
#        )

    if start is None:
        return

    checkin_time = time.perf_counter()

    held_ms = (
        checkin_time - start
    ) * 1000

    checkout_to_first_query = None
    database_lifetime = None
    after_last_query = None

    if first_query is not None:
        checkout_to_first_query = (
            first_query - start
        ) * 1000

    if first_query is not None and last_query is not None:
        database_lifetime = (
            last_query - first_query
        ) * 1000

    if last_query is not None:
        after_last_query = (
            checkin_time - last_query
        ) * 1000

    pool_metrics["longest_connection_ms"] = max(
        pool_metrics["longest_connection_ms"],
        held_ms,
    )

#    logger.info(
#        "[POOL] CHECKIN %s held %.2f ms",
#        connection_uuid,
#        held_ms,
#    )

    if held_ms > 1000:
        logger.warning(
            "\n"
            "================ CONNECTION TIMELINE ================\n"
            "Held                : %.2f ms\n"
            "Checkout -> SQL     : %s ms\n"
            "SQL Active          : %s ms\n"
            "SQL -> Checkin      : %s ms\n"
            "Queries             : %d\n"
            "Checked Out         : %d\n"
            "Peak                : %d\n"
            "Last SQL            : %s\n"
            "====================================================",
            held_ms,
            (
                f"{checkout_to_first_query:.2f}"
                if checkout_to_first_query is not None
                else "-"
            ),
            (
                f"{database_lifetime:.2f}"
                if database_lifetime is not None
                else "-"
            ),
            (
                f"{after_last_query:.2f}"
                if after_last_query is not None
                else "-"
            ),
            query_count,
            pool_metrics["checked_out"],
            pool_metrics["peak_checked_out"],
            (
                last_sql.replace("\n", " ")
                if last_sql
                else "<none>"
            ),
        )
        # Dump the entire pool if we're approaching exhaustion
#        if pool_metrics["checked_out"] >= 18:
#            log_pool_state()

# --------------------------------------------------
# SQL Timeline Instrumentation
# --------------------------------------------------

@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(
    conn,
    cursor,
    statement,
    parameters,
    context,
    executemany,
):
    record = conn.connection._connection_record
    info = record.info

    now = time.perf_counter()

    if info.get("first_query_time") is None:
        info["first_query_time"] = now



@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(
    conn,
    cursor,
    statement,
    parameters,
    context,
    executemany,
):
    record = conn.connection._connection_record
    info = record.info

    info["last_query_time"] = time.perf_counter()
    info["last_query_sql"] = statement[:120]
    info["query_count"] += 1



# --------------------------------------------------
# Session factory (UNCHANGED)
# --------------------------------------------------

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)
     
# --------------------------------------------------
# FastAPI dependency (UNCHANGED)
# --------------------------------------------------


def get_db():
    session_start = perf_counter()

    db: Session = SessionLocal()

    try:
        yield db

    finally:

        lifetime_ms = round(
            (perf_counter() - session_start) * 1000,
            3,
        )

        close_start = perf_counter()

        db.close()

        close_ms = round(
            (perf_counter() - close_start) * 1000,
            3,
        )

        logger.info(
            "db_session_close",
            extra={
                "request_id": get_request_id(),
                "session_lifetime_ms": lifetime_ms,
                "close_ms": close_ms,
            },
        )

def log_pool_state():
    snapshot = dump_pool_state()

    logger.error("========== POOL STATE ==========")

    for conn in snapshot:
        logger.error(
            "Conn=%s held=%ss pid=%s thread=%s\n%s",
            conn["connection_id"],
            conn["held_seconds"],
            conn["pid"],
            conn["thread"],
            conn["stack"],
        )

    logger.error("================================")

def dump_pool_state():
    with _pool_lock:
        snapshot = []

        now = time.time()

        for conn_id, info in active_connections.items():
            snapshot.append({
                "connection_id": conn_id,
                "held_seconds": round(now - info["checkout_time"], 3),
                "pid": info["pid"],
                "thread": info["thread"],
                "stack": info["stack"],
            })

    return snapshot