"""Конфигурация и фикстуры для тестов."""
import pytest
import pytest_asyncio
import tempfile
import os
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from database.base import Base
from database.models import User, Partner, CycleEntry, Notification


@pytest_asyncio.fixture(scope="function")
async def test_db_session():
    """Создает тестовую базу данных и сессию для каждого теста."""
    # Создаем временный файл базы данных вместо in-memory
    # Это более надежно для async операций с SQLite
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    test_db_url = f"sqlite+aiosqlite:///{temp_db.name}"
    
    try:
        test_engine = create_async_engine(
            test_db_url,
            echo=False,
            poolclass=NullPool,
        )
        
        # Создаем все таблицы через engine до создания сессии
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Создаем sessionmaker для тестов
        test_session_maker = async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        # Создаем сессию для теста
        async with test_session_maker() as session:
            yield session
        
        # Закрываем engine после теста
        await test_engine.dispose()
    finally:
        # Удаляем временный файл базы данных
        if os.path.exists(temp_db.name):
            os.unlink(temp_db.name)


@pytest_asyncio.fixture
async def test_user(test_db_session: AsyncSession):
    """Создает тестового пользователя."""
    user = User(
        telegram_id=123456789,
        username="test_user",
        cycle_length=28,
        last_period_date=datetime(2024, 1, 1),
        notification_enabled=True,
        notification_time="09:00",
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_partner(test_db_session: AsyncSession, test_user: User):
    """Создает тестового партнера для пользователя."""
    partner = Partner(
        telegram_id=987654321,
        username="test_partner",
        user_id=test_user.id,
    )
    test_db_session.add(partner)
    await test_db_session.commit()
    await test_db_session.refresh(partner)
    return partner
