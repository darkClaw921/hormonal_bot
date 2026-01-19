"""Обработчики настроек пользователя."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from keyboards.main import get_main_menu
from keyboards.settings import (
    get_settings_keyboard,
    get_notifications_toggle_keyboard,
    get_cycle_length_keyboard,
    get_notification_time_keyboard
)

router = Router()


@router.callback_query(F.data == "settings_back")
async def handle_settings_back(callback: CallbackQuery) -> None:
    """
    Обработчик кнопки "Назад" в настройках.
    
    Возвращает пользователя в главное меню.
    
    Args:
        callback: Callback запрос
    """
    await callback.message.edit_text(
        "🏠 Главное меню",
        reply_markup=None
    )
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=get_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "settings_notifications")
async def handle_settings_notifications(
    callback: CallbackQuery,
    db_session: AsyncSession
) -> None:
    """
    Обработчик кнопки "Уведомления" в настройках.
    
    Показывает текущее состояние уведомлений и кнопку переключения.
    
    Args:
        callback: Callback запрос
        db_session: Сессия базы данных
    """
    telegram_id = callback.from_user.id
    
    # Получаем пользователя
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        await callback.answer("❌ Пользователь не найден.", show_alert=True)
        return
    
    status_text = "✅ включены" if user.notification_enabled else "❌ выключены"
    keyboard = get_notifications_toggle_keyboard(user.notification_enabled)
    
    await callback.message.edit_text(
        f"🔔 **Уведомления**\n\n"
        f"Текущий статус: {status_text}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "settings_notifications_toggle")
async def handle_notifications_toggle(
    callback: CallbackQuery,
    db_session: AsyncSession
) -> None:
    """
    Обработчик переключения уведомлений.
    
    Args:
        callback: Callback запрос
        db_session: Сессия базы данных
    """
    telegram_id = callback.from_user.id
    
    # Получаем пользователя
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        await callback.answer("❌ Пользователь не найден.", show_alert=True)
        return
    
    # Переключаем уведомления
    user.notification_enabled = not user.notification_enabled
    await db_session.commit()
    
    status_text = "✅ включены" if user.notification_enabled else "❌ выключены"
    keyboard = get_notifications_toggle_keyboard(user.notification_enabled)
    
    await callback.message.edit_text(
        f"🔔 **Уведомления**\n\n"
        f"Текущий статус: {status_text}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer(f"Уведомления {status_text}")


@router.callback_query(F.data == "settings_cycle_length")
async def handle_settings_cycle_length(callback: CallbackQuery) -> None:
    """
    Обработчик кнопки "Длина цикла" в настройках.
    
    Показывает клавиатуру для выбора длины цикла.
    
    Args:
        callback: Callback запрос
    """
    keyboard = get_cycle_length_keyboard()
    
    await callback.message.edit_text(
        "📏 **Длина цикла**\n\n"
        "Выберите длину вашего менструального цикла:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("settings_cycle_length_"))
async def handle_cycle_length_selection(
    callback: CallbackQuery,
    db_session: AsyncSession
) -> None:
    """
    Обработчик выбора длины цикла.
    
    Args:
        callback: Callback запрос
        db_session: Сессия базы данных
    """
    telegram_id = callback.from_user.id
    
    # Извлекаем длину цикла из callback_data
    cycle_length_str = callback.data.split("_")[-1]
    try:
        cycle_length = int(cycle_length_str)
    except ValueError:
        await callback.answer("❌ Ошибка при выборе длины цикла.", show_alert=True)
        return
    
    # Получаем пользователя
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        await callback.answer("❌ Пользователь не найден.", show_alert=True)
        return
    
    # Обновляем длину цикла
    user.cycle_length = cycle_length
    await db_session.commit()
    
    await callback.message.edit_text(
        f"✅ **Длина цикла обновлена**\n\n"
        f"Новая длина цикла: {cycle_length} дней",
        reply_markup=get_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer(f"Длина цикла установлена: {cycle_length} дней")


@router.callback_query(F.data == "settings_notification_time")
async def handle_settings_notification_time(
    callback: CallbackQuery,
    db_session: AsyncSession
) -> None:
    """
    Обработчик кнопки "Время уведомлений" в настройках.
    
    Показывает клавиатуру для выбора времени уведомлений.
    
    Args:
        callback: Callback запрос
        db_session: Сессия базы данных
    """
    telegram_id = callback.from_user.id
    
    # Получаем пользователя
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        await callback.answer("❌ Пользователь не найден.", show_alert=True)
        return
    
    current_time = user.notification_time or "09:00"
    keyboard = get_notification_time_keyboard()
    
    await callback.message.edit_text(
        f"⏰ **Время уведомлений**\n\n"
        f"Текущее время: {current_time}\n"
        f"Выберите новое время:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("settings_time_"))
async def handle_notification_time_selection(
    callback: CallbackQuery,
    db_session: AsyncSession
) -> None:
    """
    Обработчик выбора времени уведомлений.
    
    Args:
        callback: Callback запрос
        db_session: Сессия базы данных
    """
    telegram_id = callback.from_user.id
    
    # Извлекаем время из callback_data (формат: settings_time_09:00)
    time_str = callback.data.replace("settings_time_", "")
    
    # Валидация формата времени
    try:
        hours, minutes = time_str.split(":")
        hours_int = int(hours)
        minutes_int = int(minutes)
        if not (0 <= hours_int <= 23 and 0 <= minutes_int <= 59):
            raise ValueError("Invalid time range")
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка при выборе времени.", show_alert=True)
        return
    
    # Получаем пользователя
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        await callback.answer("❌ Пользователь не найден.", show_alert=True)
        return
    
    # Обновляем время уведомлений
    user.notification_time = time_str
    await db_session.commit()
    
    await callback.message.edit_text(
        f"✅ **Время уведомлений обновлено**\n\n"
        f"Новое время: {time_str}",
        reply_markup=get_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer(f"Время уведомлений установлено: {time_str}")
