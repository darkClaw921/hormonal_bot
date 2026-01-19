"""Inline клавиатуры для ввода дня цикла."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.cycle_service import CyclePhase


def get_phase_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Создает inline клавиатуру с кнопками быстрого выбора фазы цикла.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками фаз
    """
    builder = InlineKeyboardBuilder()
    
    # Кнопки основных фаз
    builder.button(
        text="🩸 Менструация",
        callback_data="phase_menstrual"
    )
    builder.button(
        text="✨ После менструации",
        callback_data="phase_postmenstrual"
    )
    builder.button(
        text="🌺 Овуляция",
        callback_data="phase_ovulatory"
    )
    builder.button(
        text="🌙 ПМС",
        callback_data="phase_pms"
    )
    
    # Размещаем кнопки фаз по 2 в ряд
    builder.adjust(2, 2)
    
    # Дополнительные кнопки
    builder.button(
        text="🔢 Ввести число",
        callback_data="phase_manual_input"
    )
    builder.button(
        text="⏭ Пропустить",
        callback_data="phase_skip"
    )
    
    # Размещаем дополнительные кнопки по 2 в ряд
    builder.adjust(2)
    
    return builder.as_markup()
