"""Задачи планировщика для отправки уведомлений."""
import logging
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from database.engine import async_session_maker
from services.notification_service import NotificationService

logger = logging.getLogger(__name__)


async def check_phase_transitions_task(bot: Bot) -> None:
    """
    Задача для проверки переходов в новую фазу и отправки уведомлений.
    
    Выполняется ежедневно для проверки всех пользователей.
    
    Args:
        bot: Экземпляр бота для отправки сообщений
    """
    logger.info("Запуск задачи проверки переходов фаз")
    
    async with async_session_maker() as db_session:
        try:
            await NotificationService.check_and_notify_phase_transitions(
                bot,
                db_session
            )
            logger.info("Задача проверки переходов фаз завершена успешно")
        except Exception as e:
            logger.error(f"Ошибка при выполнении задачи проверки переходов фаз: {e}")


async def send_weekly_reminders_task(bot: Bot) -> None:
    """
    Задача для отправки еженедельных напоминаний пользователям.
    
    Выполняется раз в неделю для напоминания о вводе дня цикла.
    
    Args:
        bot: Экземпляр бота для отправки сообщений
    """
    logger.info("Запуск задачи отправки еженедельных напоминаний")
    
    async with async_session_maker() as db_session:
        try:
            await NotificationService.send_weekly_reminders_to_all(
                bot,
                db_session
            )
            logger.info("Задача отправки еженедельных напоминаний завершена успешно")
        except Exception as e:
            logger.error(f"Ошибка при выполнении задачи отправки напоминаний: {e}")
