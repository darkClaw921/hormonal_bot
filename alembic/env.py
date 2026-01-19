"""Alembic environment configuration для async SQLAlchemy."""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Импортируем Base и все модели для autogenerate
from database.base import Base
from database.engine import get_async_database_url
from database.models import CycleEntry, Notification, Partner, User  # noqa: F401
from bot.config import Config

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Интерпретируем config file для Python logging.
# Эта строка устанавливает loggers в основном для работы alembic.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Добавляем объект MetaData для 'autogenerate' поддержки
target_metadata = Base.metadata

# Получаем URL базы данных из конфигурации
database_url = get_async_database_url(Config.DATABASE_URL)
config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """Запускает миграции в 'offline' режиме.

    Это настраивает контекст только с URL и не требует
    Engine.  Вызывая context.execute() здесь, мы генерируем
    скрипт SQL, который будет выведен в stdout.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Выполняет миграции с переданным соединением."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Запускает миграции в 'online' режиме с async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Запускает миграции в 'online' режиме."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
