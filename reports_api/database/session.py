import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from reports_api.common.configuration import Configuration

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_db(config: Configuration) -> None:
    global _engine, _session_factory

    db_config = config.database_config
    user = db_config.get("db-user", "fabric")
    password = db_config.get("db-password", "fabric")
    database = db_config.get("db-name", "analytics")
    host = db_config.get("db-host", "reports-db:5432")

    url = f"postgresql+asyncpg://{user}:{password}@{host}/{database}"

    _engine = create_async_engine(
        url,
        pool_size=20,
        max_overflow=10,
        echo=False,
    )
    _session_factory = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)
    logger.info(f"Async database engine initialized: {host}/{database}")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def shutdown_db() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        logger.info("Async database engine disposed")
    _engine = None
    _session_factory = None
