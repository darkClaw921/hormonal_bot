"""Настройка подключения к базе данных."""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from bot.config import Config
from database.base import Base


def get_async_database_url(database_url: str) -> str:
    """
    Преобразует синхронный URL базы данных в асинхронный.
    
    Args:
        database_url: Синхронный URL базы данных
        
    Returns:
        Асинхронный URL базы данных
    """
    # Для SQLite используем aiosqlite
    if database_url.startswith("sqlite:///"):
        return database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    # Для PostgreSQL используем asyncpg (если будет использоваться)
    elif database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://")
    # Для других БД возвращаем как есть
    return database_url


# Создаем async engine
async_database_url = get_async_database_url(Config.DATABASE_URL)
engine = create_async_engine(
    async_database_url,
    echo=Config.DEBUG,
    poolclass=NullPool if "sqlite" in async_database_url else None,
)

# Создаем factory для создания сессий
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Инициализирует базу данных, создавая все таблицы."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Закрывает соединения с базой данных."""
    await engine.dispose()
