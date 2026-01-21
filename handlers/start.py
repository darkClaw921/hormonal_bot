"""Обработчики команды /start."""
from datetime import datetime
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, CycleEntry
from keyboards.main import get_main_menu
from keyboards.partners import get_partner_info_keyboard
from services.partner_service import PartnerService
from services.cycle_service import CycleService
from services.phase_formatter import PhaseFormatter
from handlers.partners import get_partner_explanation_text

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, db_session: AsyncSession) -> None:
    """
    Обработчик команды /start.
    
    Регистрирует нового пользователя в БД или приветствует существующего.
    Обрабатывает партнерские приглашения через deep linking.
    Показывает главное меню или партнерский интерфейс.
    
    Args:
        message: Сообщение от пользователя
        db_session: Сессия базы данных
    """
    telegram_id = message.from_user.id
    username = message.from_user.username
    command_args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    # Проверяем, является ли это партнерским приглашением
    if command_args and command_args[0].startswith("partner_"):
        # Это партнерское приглашение
        try:
            user_telegram_id = int(command_args[0].split("_")[1])
            
            # Получаем пользователя, который отправил приглашение
            stmt = select(User).where(User.telegram_id == user_telegram_id)
            result = await db_session.execute(stmt)
            inviting_user = result.scalar_one_or_none()
            
            if inviting_user is None:
                await message.answer(
                    "❌ Пользователь, отправивший приглашение, не найден."
                )
                return
            
            # Проверяем, не является ли это сам пользователь
            if user_telegram_id == telegram_id:
                await message.answer(
                    "❌ Вы не можете добавить себя в качестве партнера."
                )
                return
            
            # Добавляем партнера
            partner = await PartnerService.add_partner(
                db_session,
                inviting_user.id,
                telegram_id,
                username
            )
            
            if partner is None:
                await message.answer(
                    "⚠️ Вы уже были добавлены в качестве партнера или произошла ошибка."
                )
            else:
                inviting_user_name = inviting_user.username or f"Пользователь (ID: {inviting_user.telegram_id})"
                explanation_text = get_partner_explanation_text(inviting_user_name)
                await message.answer(
                    f"✅ Вы успешно добавлены в качестве партнера!\n\n"
                    f"{explanation_text}"
                )
            
            # Показываем партнерский интерфейс
            await show_partner_interface(message, db_session, telegram_id)
            return
            
        except (ValueError, IndexError):
            # Неверный формат приглашения, продолжаем как обычный /start
            pass
    
    # Обычная обработка /start
    # Проверяем, является ли пользователь партнером
    partner = await PartnerService.get_partner_by_telegram_id(db_session, telegram_id)
    
    if partner is not None:
        # Это партнер, показываем партнерский интерфейс
        await show_partner_interface(message, db_session, telegram_id)
        return
    
    # Обычный пользователь
    # Проверяем, существует ли пользователь
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        # Создаем нового пользователя
        user = User(
            telegram_id=telegram_id,
            username=username,
        )
        db_session.add(user)
        await db_session.flush()
        
        welcome_text = (
            "👋 Добро пожаловать в Hormonal Bot!\n\n"
            "Я помогу вам отслеживать ваш менструальный цикл и получать "
            "уведомления о важных фазах.\n\n"
            "Используйте меню ниже для навигации."
        )
    else:
        # Обновляем username, если он изменился
        if user.username != username:
            user.username = username
        
        welcome_text = (
            "👋 С возвращением!\n\n"
            "Используйте меню ниже для навигации."
        )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu()
    )


async def show_partner_interface(message: Message, db_session: AsyncSession, partner_telegram_id: int) -> None:
    """
    Показывает партнерский интерфейс с информацией о текущей фазе цикла партнера.
    
    Args:
        message: Сообщение от партнера
        db_session: Сессия базы данных
        partner_telegram_id: Telegram ID партнера
    """
    # Получаем пользователя по партнеру
    user = await PartnerService.get_user_by_partner_telegram_id(db_session, partner_telegram_id)
    
    if user is None:
        await message.answer(
            "❌ Не удалось найти информацию о пользователе.",
            reply_markup=None
        )
        return
    
    user_name = user.username or f"Пользователь (ID: {user.telegram_id})"
    
    # Получаем последнюю запись о цикле
    stmt = select(CycleEntry).where(
        CycleEntry.user_id == user.id
    ).order_by(CycleEntry.entry_date.desc()).limit(1)
    result = await db_session.execute(stmt)
    last_entry = result.scalar_one_or_none()
    
    if last_entry is None:
        explanation_text = get_partner_explanation_text(user_name)
        await message.answer(
            f"{explanation_text}\n\n"
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
    explanation_text = get_partner_explanation_text(user_name)
    
    await message.answer(
        f"{explanation_text}\n\n"
        f"{phase_text}",
        reply_markup=get_partner_info_keyboard(),
        parse_mode="Markdown"
    )
