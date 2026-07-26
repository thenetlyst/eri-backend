from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings



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
    db: Session = SessionLocal()
    try:
        yield db

    except Exception:
        if db.in_transaction():
            db.rollback()
        raise

    finally:

        db.close()
