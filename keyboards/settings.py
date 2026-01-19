"""Клавиатуры для настроек."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """
    Создает главную клавиатуру настроек.
    
    Returns:
        Inline клавиатура с настройками
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔔 Уведомления",
                callback_data="settings_notifications"
            )
        ],
        [
            InlineKeyboardButton(
                text="📏 Длина цикла",
                callback_data="settings_cycle_length"
            )
        ],
        [
            InlineKeyboardButton(
                text="⏰ Время уведомлений",
                callback_data="settings_notification_time"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="settings_back"
            )
        ]
    ])
    return keyboard


def get_notifications_toggle_keyboard(current_state: bool) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для переключения уведомлений.
    
    Args:
        current_state: Текущее состояние уведомлений (включены/выключены)
        
    Returns:
        Inline клавиатура с кнопками переключения
    """
    status_text = "✅ Включены" if current_state else "❌ Выключены"
    toggle_text = "❌ Выключить" if current_state else "✅ Включить"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=toggle_text,
                callback_data="settings_notifications_toggle"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="settings_back"
            )
        ]
    ])
    return keyboard


def get_cycle_length_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора длины цикла.
    
    Returns:
        Inline клавиатура с вариантами длины цикла
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="26 дней",
                callback_data="settings_cycle_length_26"
            ),
            InlineKeyboardButton(
                text="27 дней",
                callback_data="settings_cycle_length_27"
            ),
            InlineKeyboardButton(
                text="28 дней",
                callback_data="settings_cycle_length_28"
            )
        ],
        [
            InlineKeyboardButton(
                text="29 дней",
                callback_data="settings_cycle_length_29"
            ),
            InlineKeyboardButton(
                text="30 дней",
                callback_data="settings_cycle_length_30"
            ),
            InlineKeyboardButton(
                text="31 день",
                callback_data="settings_cycle_length_31"
            )
        ],
        [
            InlineKeyboardButton(
                text="32 дня",
                callback_data="settings_cycle_length_32"
            ),
            InlineKeyboardButton(
                text="33 дня",
                callback_data="settings_cycle_length_33"
            ),
            InlineKeyboardButton(
                text="34 дня",
                callback_data="settings_cycle_length_34"
            )
        ],
        [
            InlineKeyboardButton(
                text="35 дней",
                callback_data="settings_cycle_length_35"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="settings_back"
            )
        ]
    ])
    return keyboard


def get_notification_time_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора времени уведомлений.
    
    Returns:
        Inline клавиатура с вариантами времени
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="08:00",
                callback_data="settings_time_08:00"
            ),
            InlineKeyboardButton(
                text="09:00",
                callback_data="settings_time_09:00"
            ),
            InlineKeyboardButton(
                text="10:00",
                callback_data="settings_time_10:00"
            )
        ],
        [
            InlineKeyboardButton(
                text="11:00",
                callback_data="settings_time_11:00"
            ),
            InlineKeyboardButton(
                text="12:00",
                callback_data="settings_time_12:00"
            ),
            InlineKeyboardButton(
                text="13:00",
                callback_data="settings_time_13:00"
            )
        ],
        [
            InlineKeyboardButton(
                text="14:00",
                callback_data="settings_time_14:00"
            ),
            InlineKeyboardButton(
                text="15:00",
                callback_data="settings_time_15:00"
            ),
            InlineKeyboardButton(
                text="16:00",
                callback_data="settings_time_16:00"
            )
        ],
        [
            InlineKeyboardButton(
                text="17:00",
                callback_data="settings_time_17:00"
            ),
            InlineKeyboardButton(
                text="18:00",
                callback_data="settings_time_18:00"
            ),
            InlineKeyboardButton(
                text="19:00",
                callback_data="settings_time_19:00"
            )
        ],
        [
            InlineKeyboardButton(
                text="20:00",
                callback_data="settings_time_20:00"
            ),
            InlineKeyboardButton(
                text="21:00",
                callback_data="settings_time_21:00"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="settings_back"
            )
        ]
    ])
    return keyboard
