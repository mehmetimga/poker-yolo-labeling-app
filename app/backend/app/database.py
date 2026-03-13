import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


_COLUMN_MIGRATIONS = [
    ("images", "labeled_by", "INTEGER REFERENCES users(id)"),
    ("images", "labeled_at", "DATETIME"),
    ("images", "reviewed_by", "INTEGER REFERENCES users(id)"),
    ("images", "reviewed_at", "DATETIME"),
    ("annotations", "created_by", "INTEGER REFERENCES users(id)"),
]


async def run_column_migrations(conn):
    """Idempotent ALTER TABLE ADD COLUMN for new nullable columns on existing tables."""
    for table, column, col_type in _COLUMN_MIGRATIONS:
        try:
            await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
            logger.info(f"Added column {table}.{column}")
        except Exception:
            pass  # Column already exists


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await run_column_migrations(conn)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
