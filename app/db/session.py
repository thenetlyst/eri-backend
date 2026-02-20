from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

# --------------------------------------------------
# Engine
# --------------------------------------------------

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

# --------------------------------------------------
# Session factory
# --------------------------------------------------

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# --------------------------------------------------
# FastAPI dependency
# --------------------------------------------------

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()