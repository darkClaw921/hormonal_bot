"""Middleware для инжекции сессии базы данных в handlers."""
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from database.engine import async_session_maker


class DatabaseMiddleware(BaseMiddleware):
    """Middleware для создания и инжекции сессии БД в handlers."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Создает сессию БД, инжектирует её в data и гарантирует закрытие после выполнения handler.
        
        Args:
            handler: Обработчик события
            event: Событие Telegram
            data: Контекстные данные для передачи в handler
            
        Returns:
            Результат выполнения handler
        """
        async with async_session_maker() as session:
            # Инжектируем сессию в data для использования в handlers
            data["db_session"] = session
            
            try:
                # Выполняем handler
                result = await handler(event, data)
                # Коммитим изменения если все прошло успешно
                await session.commit()
                return result
            except Exception:
                # Откатываем транзакцию при ошибке
                await session.rollback()
                raise
            finally:
                # Сессия автоматически закроется благодаря context manager
                pass
