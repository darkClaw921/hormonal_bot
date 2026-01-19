"""Клавиатуры для управления партнерами."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from database.models import Partner


def get_partners_menu() -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру меню управления партнерами.
    
    Returns:
        Reply клавиатура с кнопками управления партнерами
    """
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="➕ Добавить партнера"))
    builder.add(KeyboardButton(text="📋 Список партнеров"))
    builder.add(KeyboardButton(text="🔙 Главное меню"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def get_partners_list_keyboard(partners: list[Partner]) -> InlineKeyboardMarkup:
    """
    Создает inline клавиатуру со списком партнеров для удаления.
    
    Args:
        partners: Список партнеров пользователя
        
    Returns:
        Inline клавиатура с кнопками удаления партнеров
    """
    builder = InlineKeyboardBuilder()
    
    for partner in partners:
        partner_name = partner.username or f"ID: {partner.telegram_id}"
        builder.add(InlineKeyboardButton(
            text=f"❌ Удалить {partner_name}",
            callback_data=f"remove_partner:{partner.id}"
        ))
    
    if not partners:
        builder.add(InlineKeyboardButton(
            text="Нет партнеров",
            callback_data="no_partners"
        ))
    
    builder.adjust(1)
    return builder.as_markup()


def get_confirm_remove_partner_keyboard(partner_id: int) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру подтверждения удаления партнера.
    
    Args:
        partner_id: ID партнера для удаления
        
    Returns:
        Inline клавиатура с кнопками подтверждения
    """
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="✅ Да, удалить",
        callback_data=f"confirm_remove:{partner_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="❌ Отмена",
        callback_data="cancel_remove"
    ))
    builder.adjust(2)
    return builder.as_markup()


def get_partner_info_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для партнерского интерфейса.
    
    Returns:
        Inline клавиатура с кнопкой обновления информации
    """
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="🔄 Обновить информацию",
        callback_data="refresh_partner_info"
    ))
    return builder.as_markup()
