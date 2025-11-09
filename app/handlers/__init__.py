"""Обработчики команд и сообщений."""
from aiogram import Router
from app.handlers import start, order

def setup_routers() -> Router:
    """Регистрирует все роутеры."""
    router = Router()
    router.include_router(order.order_router)  # Сначала order, чтобы перехватывать FSM
    router.include_router(start.start_router)
    return router

