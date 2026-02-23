from logging.config import fileConfig

from sqlalchemy import pool
from alembic import context

import sys
import os
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


# ---------------- OFFLINE ----------------

def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    url = os.getenv("DATABASE_URL")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------- ONLINE ----------------

def run_migrations_online() -> None:
    """Run migrations in online mode using DATABASE_URL env."""

    from sqlalchemy import create_engine

    database_url = os.getenv("DATABASE_URL")

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


# ---------------- ENTRY ----------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()