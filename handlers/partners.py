"""Обработчики для управления партнерами."""
from datetime import datetime
from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Partner, User
from keyboards.partners import (
    get_partners_menu,
    get_partners_list_keyboard,
    get_confirm_remove_partner_keyboard,
    get_partner_info_keyboard
)
from keyboards.main import get_main_menu
from services.partner_service import PartnerService
from services.cycle_service import CycleService
from services.phase_formatter import PhaseFormatter

router = Router()

# Состояния для FSM (можно использовать aiogram FSM, но для простоты используем словарь)
# В реальном проекте лучше использовать aiogram FSM
_waiting_for_partner_id: dict[int, bool] = {}


@router.message(F.text == "Партнеры")
async def handle_partners_menu(message: Message, db_session: AsyncSession) -> None:
    """
    Обработчик кнопки "Партнеры".
    
    Показывает меню управления партнерами.
    
    Args:
        message: Сообщение от пользователя
        db_session: Сессия базы данных
    """
    await message.answer(
        "👥 Управление партнерами\n\n"
        "Выберите действие:",
        reply_markup=get_partners_menu()
    )


@router.message(F.text == "➕ Добавить партнера")
async def handle_add_partner_start(message: Message, db_session: AsyncSession, bot: Bot) -> None:
    """
    Обработчик начала добавления партнера.
    
    Запрашивает у пользователя Telegram ID или username партнера.
    
    Args:
        message: Сообщение от пользователя
        db_session: Сессия базы данных
        bot: Экземпляр бота для получения информации о боте
    """
    telegram_id = message.from_user.id
    _waiting_for_partner_id[telegram_id] = True
    
    # Получаем информацию о боте для генерации ссылки
    try:
        bot_info = await bot.get_me()
        bot_username = bot_info.username
        invite_link = f"https://t.me/{bot_username}?start=partner_{telegram_id}"
    except Exception:
        invite_link = f"https://t.me/your_bot?start=partner_{telegram_id}"
    
    await message.answer(
        "➕ Добавление партнера\n\n"
        "Отправьте мне Telegram ID или username партнера.\n"
        "Например:\n"
        "• 123456789 (Telegram ID)\n"
        "• @username (username)\n\n"
        "Или отправьте партнеру ссылку-приглашение:\n"
        f"{invite_link}",
        reply_markup=get_partners_menu()
    )


@router.message(F.text == "📋 Список партнеров")
async def handle_list_partners(message: Message, db_session: AsyncSession) -> None:
    """
    Обработчик показа списка партнеров.
    
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
            "❌ Пользователь не найден. Пожалуйста, используйте команду /start.",
            reply_markup=get_main_menu()
        )
        return
    
    # Получаем список партнеров
    partners = await PartnerService.get_partners(db_session, user.id)
    
    if not partners:
        await message.answer(
            "📋 У вас пока нет добавленных партнеров.\n\n"
            "Используйте кнопку '➕ Добавить партнера' для добавления.",
            reply_markup=get_partners_menu()
        )
        return
    
    partners_text = "📋 Ваши партнеры:\n\n"
    for i, partner in enumerate(partners, 1):
        # Формируем информацию о партнере
        partner_info_parts = []
        
        if partner.username:
            partner_info_parts.append(f"@{partner.username}")
        partner_info_parts.append(f"ID: {partner.telegram_id}")
        
        # Форматируем дату добавления
        if partner.created_at:
            date_str = partner.created_at.strftime("%d.%m.%Y")
            partner_info_parts.append(f"Добавлен: {date_str}")
        
        partner_info = " | ".join(partner_info_parts)
        partners_text += f"{i}. {partner_info}\n"
    
    await message.answer(
        partners_text,
        reply_markup=get_partners_list_keyboard(partners)
    )


@router.message(F.text == "🔙 Главное меню")
async def handle_back_to_main(message: Message, db_session: AsyncSession) -> None:
    """
    Обработчик возврата в главное меню.
    
    Args:
        message: Сообщение от пользователя
        db_session: Сессия базы данных
    """
    telegram_id = message.from_user.id
    _waiting_for_partner_id.pop(telegram_id, None)
    
    await message.answer(
        "🔙 Возврат в главное меню",
        reply_markup=get_main_menu()
    )


@router.message(lambda message: message.from_user.id in _waiting_for_partner_id)
async def handle_partner_id_input(message: Message, db_session: AsyncSession, bot: Bot) -> None:
    """
    Обработчик ввода Telegram ID или username партнера.
    
    Args:
        message: Сообщение от пользователя
        db_session: Сессия базы данных
        bot: Экземпляр бота для отправки сообщений партнеру
    """
    telegram_id = message.from_user.id
    _waiting_for_partner_id.pop(telegram_id, None)
    
    # Получаем пользователя
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        await message.answer(
            "❌ Пользователь не найден. Пожалуйста, используйте команду /start.",
            reply_markup=get_main_menu()
        )
        return
    
    input_text = message.text.strip()
    partner_telegram_id = None
    partner_username = None
    
    # Парсим ввод
    if input_text.startswith("@"):
        # Это username
        partner_username = input_text[1:]
        # Получаем информацию о боте для генерации ссылки
        try:
            bot_info = await bot.get_me()
            bot_username = bot_info.username
            invite_link = f"https://t.me/{bot_username}?start=partner_{telegram_id}"
        except Exception:
            invite_link = f"https://t.me/your_bot?start=partner_{telegram_id}"
        
        # Пытаемся получить информацию о пользователе через бота
        try:
            # В aiogram 3.x нет прямого способа получить user по username
            # Поэтому просим пользователя отправить ID или использовать ссылку
            await message.answer(
                "⚠️ Для добавления по username попросите партнера отправить вам его Telegram ID "
                "или используйте ссылку-приглашение:\n"
                f"{invite_link}\n\n"
                "Telegram ID можно узнать у бота @userinfobot",
                reply_markup=get_partners_menu()
            )
            return
        except Exception:
            await message.answer(
                "❌ Не удалось найти пользователя по username. "
                f"Попросите партнера отправить вам его Telegram ID или используйте ссылку-приглашение:\n{invite_link}",
                reply_markup=get_partners_menu()
            )
            return
    elif input_text.isdigit():
        # Это Telegram ID
        partner_telegram_id = int(input_text)
    else:
        await message.answer(
            "❌ Неверный формат. Отправьте Telegram ID (число) или username (начинается с @).",
            reply_markup=get_partners_menu()
        )
        return
    
    if partner_telegram_id is None:
        await message.answer(
            "❌ Не удалось определить Telegram ID партнера.",
            reply_markup=get_partners_menu()
        )
        return
    
    # Проверяем, не является ли это сам пользователь
    if partner_telegram_id == telegram_id:
        await message.answer(
            "❌ Вы не можете добавить себя в качестве партнера.",
            reply_markup=get_partners_menu()
        )
        return
    
    # Добавляем партнера
    partner = await PartnerService.add_partner(
        db_session,
        user.id,
        partner_telegram_id,
        partner_username
    )
    
    if partner is None:
        await message.answer(
            "❌ Не удалось добавить партнера. Возможно, он уже добавлен или произошла ошибка.",
            reply_markup=get_partners_menu()
        )
        return
    
    # Отправляем уведомление партнеру
    try:
        partner_name = user.username or f"Пользователь (ID: {user.telegram_id})"
        await bot.send_message(
            partner_telegram_id,
            f"👋 Вас добавили в качестве партнера!\n\n"
            f"Пользователь {partner_name} добавил вас для получения уведомлений о фазах цикла.\n\n"
            f"Используйте команду /start для просмотра информации о текущей фазе."
        )
    except Exception:
        # Если не удалось отправить сообщение партнеру, это не критично
        pass
    
    partner_display = partner_username or str(partner_telegram_id)
    await message.answer(
        f"✅ Партнер {partner_display} успешно добавлен!\n\n"
        f"Партнер получит уведомления о важных фазах вашего цикла.",
        reply_markup=get_partners_menu()
    )


@router.callback_query(lambda c: c.data and c.data.startswith("remove_partner:"))
async def handle_remove_partner_callback(callback: CallbackQuery, db_session: AsyncSession) -> None:
    """
    Обработчик callback для удаления партнера.
    
    Args:
        callback: Callback запрос
        db_session: Сессия базы данных
    """
    partner_id = int(callback.data.split(":")[1])
    
    # Получаем партнера для отображения информации
    stmt = select(Partner).where(Partner.id == partner_id)
    result = await db_session.execute(stmt)
    partner = result.scalar_one_or_none()
    
    if partner is None:
        await callback.answer("❌ Партнер не найден", show_alert=True)
        return
    
    partner_name = partner.username or f"ID: {partner.telegram_id}"
    await callback.message.edit_text(
        f"⚠️ Вы уверены, что хотите удалить партнера {partner_name}?",
        reply_markup=get_confirm_remove_partner_keyboard(partner_id)
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("confirm_remove:"))
async def handle_confirm_remove_partner(callback: CallbackQuery, db_session: AsyncSession) -> None:
    """
    Обработчик подтверждения удаления партнера.
    
    Args:
        callback: Callback запрос
        db_session: Сессия базы данных
    """
    partner_id = int(callback.data.split(":")[1])
    telegram_id = callback.from_user.id
    
    # Получаем пользователя
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    
    # Удаляем партнера
    success = await PartnerService.remove_partner(db_session, user.id, partner_id)
    
    if success:
        await callback.message.edit_text("✅ Партнер успешно удален!")
        await callback.answer("Партнер удален")
    else:
        await callback.answer("❌ Не удалось удалить партнера", show_alert=True)


@router.callback_query(lambda c: c.data == "cancel_remove")
async def handle_cancel_remove(callback: CallbackQuery, db_session: AsyncSession) -> None:
    """
    Обработчик отмены удаления партнера.
    
    Args:
        callback: Callback запрос
        db_session: Сессия базы данных
    """
    telegram_id = callback.from_user.id
    
    # Получаем пользователя и список партнеров
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    
    partners = await PartnerService.get_partners(db_session, user.id)
    
    if not partners:
        await callback.message.edit_text(
            "📋 У вас пока нет добавленных партнеров.",
            reply_markup=None
        )
    else:
        partners_text = "📋 Ваши партнеры:\n\n"
        for i, partner in enumerate(partners, 1):
            # Формируем информацию о партнере
            partner_info_parts = []
            
            if partner.username:
                partner_info_parts.append(f"@{partner.username}")
            partner_info_parts.append(f"ID: {partner.telegram_id}")
            
            # Форматируем дату добавления
            if partner.created_at:
                date_str = partner.created_at.strftime("%d.%m.%Y")
                partner_info_parts.append(f"Добавлен: {date_str}")
            
            partner_info = " | ".join(partner_info_parts)
            partners_text += f"{i}. {partner_info}\n"
        
        await callback.message.edit_text(
            partners_text,
            reply_markup=get_partners_list_keyboard(partners)
        )
    
    await callback.answer()


@router.callback_query(lambda c: c.data == "no_partners")
async def handle_no_partners(callback: CallbackQuery) -> None:
    """Обработчик нажатия на неактивную кнопку 'Нет партнеров'."""
    await callback.answer("У вас пока нет партнеров", show_alert=True)


@router.callback_query(lambda c: c.data == "refresh_partner_info")
async def handle_refresh_partner_info(callback: CallbackQuery, db_session: AsyncSession) -> None:
    """
    Обработчик обновления информации о цикле для партнера.
    
    Args:
        callback: Callback запрос
        db_session: Сессия базы данных
    """
    partner_telegram_id = callback.from_user.id
    
    # Получаем пользователя по партнеру
    user = await PartnerService.get_user_by_partner_telegram_id(db_session, partner_telegram_id)
    
    if user is None:
        await callback.answer("❌ Не удалось найти информацию о пользователе", show_alert=True)
        return
    
    user_name = user.username or f"Пользователь (ID: {user.telegram_id})"
    
    # Получаем последнюю запись о цикле
    from database.models import CycleEntry
    stmt = select(CycleEntry).where(
        CycleEntry.user_id == user.id
    ).order_by(CycleEntry.entry_date.desc()).limit(1)
    result = await db_session.execute(stmt)
    last_entry = result.scalar_one_or_none()
    
    if last_entry is None:
        await callback.message.edit_text(
            f"👥 Вы являетесь партнером пользователя {user_name}.\n\n"
            f"📅 Информация о цикле пока недоступна.\n"
            f"Пользователь еще не ввел данные о своем цикле.",
            reply_markup=get_partner_info_keyboard()
        )
        await callback.answer("Информация обновлена")
        return
    
    # Определяем текущую фазу
    cycle_length = user.cycle_length or 28
    phase_info = CycleService.get_phase_info(last_entry.day_number, cycle_length)
    
    if phase_info is None:
        await callback.message.edit_text(
            f"👥 Вы являетесь партнером пользователя {user_name}.\n\n"
            f"❌ Не удалось определить текущую фазу цикла.",
            reply_markup=get_partner_info_keyboard()
        )
        await callback.answer("Информация обновлена")
        return
    
    # Форматируем информацию о фазе с советами для партнера
    phase_text = PhaseFormatter.format_phase_info(phase_info, include_partner_advice=True)
    
    await callback.message.edit_text(
        f"👥 Вы являетесь партнером пользователя {user_name}.\n\n"
        f"{phase_text}",
        reply_markup=get_partner_info_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer("Информация обновлена")


@router.message(Command("partner"))
async def handle_partner_command(message: Message, db_session: AsyncSession) -> None:
    """
    Обработчик команды /partner для партнеров.
    
    Показывает информацию о текущей фазе цикла партнера.
    
    Args:
        message: Сообщение от партнера
        db_session: Сессия базы данных
    """
    partner_telegram_id = message.from_user.id
    
    # Получаем пользователя по партнеру
    user = await PartnerService.get_user_by_partner_telegram_id(db_session, partner_telegram_id)
    
    if user is None:
        await message.answer(
            "❌ Вы не являетесь партнером какого-либо пользователя.\n\n"
            "Попросите пользователя добавить вас в качестве партнера."
        )
        return
    
    user_name = user.username or f"Пользователь (ID: {user.telegram_id})"
    
    # Получаем последнюю запись о цикле
    from database.models import CycleEntry
    stmt = select(CycleEntry).where(
        CycleEntry.user_id == user.id
    ).order_by(CycleEntry.entry_date.desc()).limit(1)
    result = await db_session.execute(stmt)
    last_entry = result.scalar_one_or_none()
    
    if last_entry is None:
        await message.answer(
            f"👥 Вы являетесь партнером пользователя {user_name}.\n\n"
            f"📅 Информация о цикле пока недоступна.\n"
            f"Пользователь еще не ввел данные о своем цикле.",
            reply_markup=get_partner_info_keyboard()
        )
        return
    
    # Определяем текущую фазу
    cycle_length = user.cycle_length or 28
    phase_info = CycleService.get_phase_info(last_entry.day_number, cycle_length)
    
    if phase_info is None:
        await message.answer(
            f"👥 Вы являетесь партнером пользователя {user_name}.\n\n"
            f"❌ Не удалось определить текущую фазу цикла.",
            reply_markup=get_partner_info_keyboard()
        )
        return
    
    # Форматируем информацию о фазе с советами для партнера
    phase_text = PhaseFormatter.format_phase_info(phase_info, include_partner_advice=True)
    
    await message.answer(
        f"👥 Вы являетесь партнером пользователя {user_name}.\n\n"
        f"{phase_text}",
        reply_markup=get_partner_info_keyboard(),
        parse_mode="Markdown"
    )
