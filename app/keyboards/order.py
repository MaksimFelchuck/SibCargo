"""Клавиатуры для оформления заказа."""
from datetime import datetime, timedelta
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_calendar import SimpleCalendar


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены."""
    keyboard = [[KeyboardButton(text="❌ Отменить")]]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )


def get_location_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для ввода адреса."""
    keyboard = [
        [KeyboardButton(text="❌ Отменить")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


async def get_date_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура-календарь для выбора даты."""
    calendar = SimpleCalendar(
        locale='ru_RU.UTF-8',
        cancel_btn='Отмена',
        today_btn='Сегодня'
    )
    return await calendar.start_calendar()


def get_time_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора времени."""
    times = [
        "08:00", "09:00", "10:00", "11:00",
        "12:00", "13:00", "14:00", "15:00",
        "16:00", "17:00", "18:00", "19:00"
    ]
    
    buttons = []
    row = []
    
    for i, time in enumerate(times):
        row.append(InlineKeyboardButton(
            text=time,
            callback_data=f"time_{time}"
        ))
        
        # По 3 кнопки в ряд
        if (i + 1) % 3 == 0:
            buttons.append(row)
            row = []
    
    # Добавляем оставшиеся кнопки
    if row:
        buttons.append(row)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения заказа."""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_order"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

