"""Клавиатуры главного меню."""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu() -> ReplyKeyboardMarkup:
    """Создаёт клавиатуру главного меню."""
    keyboard = [
        [KeyboardButton(text="🚚 Оформить перевозку")],
        [KeyboardButton(text="ℹ️ О нас"), KeyboardButton(text="📦 Мои заказы")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )

