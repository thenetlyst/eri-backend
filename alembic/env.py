from logging.config import fileConfig

from sqlalchemy import pool, create_engine
from alembic import context

import sys
import os

# -----------------------------
# LOAD ENV
# -----------------------------
from dotenv import load_dotenv
load_dotenv(override=False)

# Ensure project root is included
sys.path.append(os.getcwd())

# Alembic Config object
config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import metadata
from app.db.base import Base
from app import models

target_metadata = Base.metadata


# -----------------------------
# OFFLINE MODE
# -----------------------------
def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    url = os.getenv("DATABASE_URL")

    if not url:
        raise RuntimeError("❌ DATABASE_URL not found in environment")

    print("🔥 ALEMBIC OFFLINE DB:", url)

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# -----------------------------
# ONLINE MODE
# -----------------------------
def run_migrations_online() -> None:
    """Run migrations in online mode."""

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("❌ DATABASE_URL not found in environment")

    print("🔥 ALEMBIC USING DB:", database_url)

    connectable = create_engine(
        database_url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# -----------------------------
# ENTRY POINT
# -----------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()