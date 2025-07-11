import asyncio
from logging.config import fileConfig

from sqlalchemy import pool, create_engine
from alembic import context

from core.config.settings import settings
from api.db.base import Base
from api.v1.models import user
from api.v1.models.base_class import Base 
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

print("POSTGRES_SERVER:", os.getenv("POSTGRES_SERVER"))

target_metadata = Base.metadata


config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def get_sync_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg"):
        return database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
    return database_url

config.set_main_option("sqlalchemy.url", get_sync_database_url(settings.SQLALCHEMY_DATABASE_URI))

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
