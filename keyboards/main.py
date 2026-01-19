"""Главное меню бота."""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_menu() -> ReplyKeyboardMarkup:
    """
    Создает главное меню с кнопками.
    
    Returns:
        ReplyKeyboardMarkup: Клавиатура главного меню
    """
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="Мой цикл")
    builder.button(text="Ввести день цикла")
    builder.button(text="Партнеры")
    builder.button(text="Настройки")
    
    # Размещаем кнопки по 2 в ряд
    builder.adjust(2, 2)
    
    return builder.as_markup(resize_keyboard=True)


def get_remove_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает пустую клавиатуру для удаления текущей клавиатуры.
    
    Returns:
        ReplyKeyboardMarkup: Пустая клавиатура
    """
    return ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True)
