"""Точка входа в приложение."""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from bot.config import Config, setup_logging
from database.engine import close_db, init_db
from middlewares.database import DatabaseMiddleware
from routers import main_router
from tasks.notifications import check_phase_transitions_task, send_weekly_reminders_task


async def main() -> None:
    """Основная функция запуска бота."""
    # Настраиваем логирование
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Валидируем конфигурацию
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Ошибка конфигурации: {e}")
        return
    
    # Инициализируем базу данных
    try:
        await init_db()
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")
        return
    
    # Создаем бота и диспетчер
    bot = Bot(
        token=Config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Подключаем middleware
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    
    # Подключаем роутеры
    dp.include_router(main_router)
    
    logger.info("Бот запущен")
    
    # Настраиваем планировщик задач
    scheduler = AsyncIOScheduler()
    scheduler.start()
    
    # Добавляем задачу проверки переходов фаз (ежедневно)
    scheduler.add_job(
        check_phase_transitions_task,
        IntervalTrigger(days=1),
        id="check_phase_transitions",
        kwargs={"bot": bot},
        replace_existing=True
    )
    
    # Добавляем задачу еженедельных напоминаний (каждую неделю)
    scheduler.add_job(
        send_weekly_reminders_task,
        IntervalTrigger(weeks=1),
        id="send_weekly_reminders",
        kwargs={"bot": bot},
        replace_existing=True
    )
    
    logger.info("Планировщик задач настроен")
    
    try:
        # Запускаем polling
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}")
    finally:
        # Останавливаем планировщик
        scheduler.shutdown()
        # Закрываем соединения
        await close_db()
        await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())
