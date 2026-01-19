"""Обработчики кнопок главного меню."""
from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from keyboards.cycle_input import get_phase_selection_keyboard
from services.statistics_service import StatisticsService

router = Router()


@router.message(F.text == "Мой цикл")
async def handle_my_cycle(message: Message, db_session: AsyncSession) -> None:
    """
    Обработчик кнопки "Мой цикл".
    
    Показывает статистику циклов пользователя.
    
    Args:
        message: Сообщение от пользователя
        db_session: Сессия базы данных
    """
    telegram_id = message.from_user.id
    
    # Получаем пользователя
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        await message.answer(
            "❌ Пользователь не найден. Пожалуйста, используйте команду /start."
        )
        return
    
    # Получаем статистику
    stats = await StatisticsService.get_user_statistics(user, db_session)
    
    # Форматируем и отправляем статистику
    stats_text = StatisticsService.format_statistics(stats)
    await message.answer(stats_text, parse_mode="Markdown")


@router.message(F.text == "Ввести день цикла")
async def handle_enter_day(message: Message, db_session: AsyncSession) -> None:
    """
    Обработчик кнопки "Ввести день цикла".
    
    Показывает inline клавиатуру с кнопками быстрого выбора фазы.
    
    Args:
        message: Сообщение от пользователя
        db_session: Сессия базы данных
    """
    keyboard = get_phase_selection_keyboard()
    await message.answer(
        "📝 Выберите фазу цикла или введите день вручную:",
        reply_markup=keyboard
    )




@router.message(F.text == "Настройки")
async def handle_settings(message: Message, db_session: AsyncSession) -> None:
    """
    Обработчик кнопки "Настройки".
    
    Показывает меню настроек пользователя.
    
    Args:
        message: Сообщение от пользователя
        db_session: Сессия базы данных
    """
    from sqlalchemy import select
    from database.models import User
    from keyboards.settings import get_settings_keyboard
    
    telegram_id = message.from_user.id
    
    # Получаем пользователя
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        await message.answer(
            "❌ Пользователь не найден. Пожалуйста, используйте команду /start."
        )
        return
    
    # Формируем информацию о текущих настройках
    notification_status = "✅ включены" if user.notification_enabled else "❌ выключены"
    cycle_length = user.cycle_length or 28
    notification_time = user.notification_time or "09:00"
    
    settings_text = (
        "⚙️ **Настройки**\n\n"
        f"🔔 Уведомления: {notification_status}\n"
        f"📏 Длина цикла: {cycle_length} дней\n"
        f"⏰ Время уведомлений: {notification_time}\n\n"
        "Выберите настройку для изменения:"
    )
    
    keyboard = get_settings_keyboard()
    await message.answer(settings_text, reply_markup=keyboard, parse_mode="Markdown")
