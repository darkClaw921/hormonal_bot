"""Обработчики ввода дня цикла."""
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import CycleEntry, User
from services.cycle_service import CycleService, CyclePhase, PhaseInfo
from services.phase_formatter import PhaseFormatter

router = Router()


@router.message(lambda message: message.text and message.text.isdigit())
async def handle_cycle_day_input(message: Message, db_session: AsyncSession) -> None:
    """
    Обработчик ввода дня цикла.
    
    Валидирует ввод (число от 1 до 35), сохраняет в БД и показывает информацию.
    
    Args:
        message: Сообщение от пользователя
        db_session: Сессия базы данных
    """
    try:
        day_number = int(message.text)
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число от 1 до 35.")
        return
    
    # Валидация диапазона
    if day_number < 1 or day_number > 35:
        await message.answer("❌ День цикла должен быть от 1 до 35.")
        return
    
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
    
    # Определяем фазу цикла
    cycle_length = user.cycle_length or 28
    phase_info = CycleService.get_phase_info(day_number, cycle_length)
    
    if phase_info is None:
        await message.answer("❌ Не удалось определить фазу цикла.")
        return
    
    # Получаем название фазы для сохранения в БД
    phase_name = phase_info.phase.value
    
    # Проверяем, произошел ли переход в новую фазу
    # Получаем последнюю запись пользователя
    last_entry_stmt = (
        select(CycleEntry)
        .where(CycleEntry.user_id == user.id)
        .order_by(CycleEntry.entry_date.desc())
        .limit(1)
    )
    last_entry_result = await db_session.execute(last_entry_stmt)
    last_entry = last_entry_result.scalar_one_or_none()
    
    is_phase_transition = False
    if last_entry:
        is_phase_transition = CycleService.is_phase_transition(
            day_number,
            last_entry.day_number,
            cycle_length
        )
    
    # Создаем запись о дне цикла
    cycle_entry = CycleEntry(
        user_id=user.id,
        day_number=day_number,
        entry_date=datetime.now(),
        phase=phase_name,
    )
    db_session.add(cycle_entry)
    await db_session.flush()
    
    # Форматируем информацию о фазе
    phase_text = PhaseFormatter.format_phase_info(phase_info, include_partner_advice=False)
    
    # Формируем ответ
    response_text = f"✅ День цикла сохранен!\n\n{phase_text}"
    
    if is_phase_transition and last_entry:
        response_text = f"🔄 Переход в новую фазу!\n\n{response_text}"
    
    await message.answer(response_text, parse_mode="Markdown")


def calculate_day_from_phase(phase: CyclePhase, cycle_length: int = 28) -> int:
    """
    Рассчитывает примерный день цикла на основе выбранной фазы.
    Использует средний день фазы.
    
    Args:
        phase: Выбранная фаза цикла
        cycle_length: Длина цикла в днях
        
    Returns:
        Номер дня цикла
    """
    boundaries = CycleService.get_phase_boundaries(cycle_length)
    start, end = boundaries[phase]
    # Возвращаем средний день фазы
    return (start + end) // 2


async def save_cycle_entry(
    telegram_id: int,
    day_number: int,
    db_session: AsyncSession
) -> tuple[bool, str, PhaseInfo | None]:
    """
    Сохраняет запись о дне цикла в БД.
    
    Args:
        telegram_id: Telegram ID пользователя
        day_number: Номер дня цикла
        db_session: Сессия базы данных
        
    Returns:
        Tuple (success, message, phase_info)
    """
    # Получаем пользователя
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        return False, "❌ Пользователь не найден. Пожалуйста, используйте команду /start.", None
    
    # Определяем фазу цикла
    cycle_length = user.cycle_length or 28
    phase_info = CycleService.get_phase_info(day_number, cycle_length)
    
    if phase_info is None:
        return False, "❌ Не удалось определить фазу цикла.", None
    
    # Получаем название фазы для сохранения в БД
    phase_name = phase_info.phase.value
    
    # Проверяем, произошел ли переход в новую фазу
    last_entry_stmt = (
        select(CycleEntry)
        .where(CycleEntry.user_id == user.id)
        .order_by(CycleEntry.entry_date.desc())
        .limit(1)
    )
    last_entry_result = await db_session.execute(last_entry_stmt)
    last_entry = last_entry_result.scalar_one_or_none()
    
    is_phase_transition = False
    if last_entry:
        is_phase_transition = CycleService.is_phase_transition(
            day_number,
            last_entry.day_number,
            cycle_length
        )
    
    # Создаем запись о дне цикла
    cycle_entry = CycleEntry(
        user_id=user.id,
        day_number=day_number,
        entry_date=datetime.now(),
        phase=phase_name,
    )
    db_session.add(cycle_entry)
    await db_session.flush()
    
    # Форматируем информацию о фазе
    phase_text = PhaseFormatter.format_phase_info(phase_info, include_partner_advice=False)
    
    # Формируем ответ
    response_text = f"✅ День цикла сохранен!\n\n{phase_text}"
    
    if is_phase_transition and last_entry:
        response_text = f"🔄 Переход в новую фазу!\n\n{response_text}"
    
    return True, response_text, phase_info


@router.callback_query(F.data.startswith("phase_"))
async def handle_phase_selection(callback: CallbackQuery, db_session: AsyncSession) -> None:
    """
    Обработчик выбора фазы через inline кнопки.
    
    Args:
        callback: Callback запрос от inline кнопки
        db_session: Сессия базы данных
    """
    await callback.answer()
    
    callback_data = callback.data
    telegram_id = callback.from_user.id
    
    # Обработка кнопки "Пропустить"
    if callback_data == "phase_skip":
        await callback.message.edit_text("⏭ Ввод дня цикла пропущен.")
        return
    
    # Обработка кнопки "Ввести число"
    if callback_data == "phase_manual_input":
        await callback.message.edit_text(
            "📝 Введите день вашего цикла (от 1 до 35):"
        )
        return
    
    # Получаем пользователя для определения длины цикла
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        await callback.message.edit_text(
            "❌ Пользователь не найден. Пожалуйста, используйте команду /start."
        )
        return
    
    cycle_length = user.cycle_length or 28
    
    # Маппинг callback_data на фазы
    phase_mapping = {
        "phase_menstrual": CyclePhase.MENSTRUAL,
        "phase_postmenstrual": CyclePhase.POSTMENSTRUAL,
        "phase_ovulatory": CyclePhase.OVULATORY,
        "phase_pms": CyclePhase.PMS,
    }
    
    if callback_data not in phase_mapping:
        await callback.message.edit_text("❌ Неизвестная фаза.")
        return
    
    selected_phase = phase_mapping[callback_data]
    
    # Рассчитываем день цикла на основе фазы
    day_number = calculate_day_from_phase(selected_phase, cycle_length)
    
    # Сохраняем запись
    success, message_text, phase_info = await save_cycle_entry(
        telegram_id, day_number, db_session
    )
    
    if success:
        await callback.message.edit_text(message_text, parse_mode="Markdown")
    else:
        await callback.message.edit_text(message_text)
