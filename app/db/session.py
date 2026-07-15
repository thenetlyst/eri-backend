from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

import logging
import time
from sqlalchemy import event


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
    pool_size=20,          # ↑ base connections (was 20)
    max_overflow=40,      # ↑ burst capacity (was 40)
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

    with _pool_lock:
        active_connections[connection_uuid] = {
            "pid": os.getpid(),
            "thread": threading.get_ident(),
            "checkout_time": time.time(),
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

    held_ms = (time.perf_counter() - start) * 1000
    pool_metrics["longest_connection_ms"] = max(
        pool_metrics["longest_connection_ms"],
        held_ms,
    )

    if held_ms > 100:
        logger.warning(
            "[POOL] LONG CONNECTION %.2f ms | checked_out=%d | peak=%d",
            held_ms,
            pool_metrics["checked_out"],
            pool_metrics["peak_checked_out"],
        )
        
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

        logger.info(
            "db_session_lifetime",
            extra={
                "session_lifetime_ms": lifetime_ms,
            },
        )

        db.close()
        

#        logger.info(
#            "db_session_closed",
#            extra={
#                "session_close_ms": close_ms,
#            },
#        )