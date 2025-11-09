"""Обработчики команд /start, /help и главного меню."""
import logging
from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from app.keyboards.main_menu import get_main_menu
from app.db import get_async_session
from app.services import UserDBService

start_router = Router()
logger = logging.getLogger(__name__)


@start_router.message(CommandStart())
async def handle_start(message: Message) -> None:
    """Ответ на команду /start."""
    # Сохраняем или обновляем пользователя в БД
    async for session in get_async_session():
        try:
            user_service = UserDBService(session)
            user, created = await user_service.get_or_create_user(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )
            
            if created:
                logger.info(f"Новый пользователь создан: {user.telegram_id} (@{user.username})")
            else:
                logger.info(f"Пользователь обновлён: {user.telegram_id} (@{user.username})")
        except Exception as e:
            logger.error(f"Ошибка при сохранении пользователя: {e}")
    
    await message.answer(
        f"👋 Добро пожаловать в <b>SibCargo</b>!\n\n"
        f"Я помогу вам заказать грузоперевозку быстро и удобно.\n"
        f"Выберите действие из меню:",
        reply_markup=get_main_menu()
    )


@start_router.message(Command("help"))
async def handle_help(message: Message) -> None:
    """Ответ на команду /help."""
    await message.answer(
        "ℹ️ <b>Как пользоваться ботом:</b>\n\n"
        "🚚 <b>Оформить перевозку</b> — создать новую заявку\n"
        "ℹ️ <b>О нас</b> — информация о компании\n"
        "📦 <b>Мои заказы</b> — посмотреть историю заказов\n\n"
        "Для отмены действия используйте /cancel",
        reply_markup=get_main_menu()
    )


@start_router.message(lambda msg: msg.text == "ℹ️ О нас")
async def handle_about(message: Message) -> None:
    """Информация о компании."""
    await message.answer(
        "ℹ️ <b>О компании SibCargo</b>\n\n"
        "Мы предоставляем услуги грузоперевозок по Новосибирску и области.\n\n"
        "📞 <b>Контакты:</b>\n"
        "Телефон: +7 (XXX) XXX-XX-XX\n"
        "Email: info@sibcargo.ru\n\n"
        "Работаем ежедневно с 8:00 до 22:00"
    )


@start_router.message(lambda msg: msg.text == "📦 Мои заказы")
async def handle_my_orders(message: Message) -> None:
    """Показать заказы пользователя."""
    async for session in get_async_session():
        try:
            # Получаем пользователя
            user_service = UserDBService(session)
            user = await user_service.get_user_by_telegram_id(
                telegram_id=message.from_user.id
            )
            
            if not user:
                await message.answer("❌ Пользователь не найден. Нажмите /start")
                return
            
            # Получаем заказы пользователя
            from app.services import OrderDBService
            order_service = OrderDBService(session)
            orders = await order_service.get_user_orders(
                user_id=user.telegram_id,
                limit=10
            )
            
            if not orders:
                await message.answer(
                    "📦 <b>Мои заказы</b>\n\n"
                    "У вас пока нет заказов.\n"
                    "Создайте первый заказ через кнопку «🚚 Оформить перевозку»"
                )
                return
            
            # Формируем список заказов
            orders_text = "📦 <b>Ваши заказы:</b>\n\n"
            
            for order in orders:
                # Получаем строковое значение статуса и приводим к верхнему регистру
                status_value = order.status.value if hasattr(order.status, 'value') else str(order.status)
                status_value = status_value.upper()  # Приводим к верхнему регистру!
                
                status_emoji = {
                    "DRAFT": "📝",
                    "PENDING": "⏳",
                    "CONFIRMED": "✅",
                    "IN_PROGRESS": "🚚",
                    "COMPLETED": "✔️",
                    "CANCELLED": "❌"
                }.get(status_value, "❓")
                
                status_text = {
                    "DRAFT": "Черновик",
                    "PENDING": "Ожидает подтверждения",
                    "CONFIRMED": "Подтверждён",
                    "IN_PROGRESS": "В процессе доставки",
                    "COMPLETED": "Завершён",
                    "CANCELLED": "Отменён"
                }.get(status_value, "Неизвестно")
                
                orders_text += f"{status_emoji} <b>Заказ #{order.id}</b> — {status_text}\n"
                
                if order.load_address:
                    orders_text += f"📍 Откуда: {order.load_address[:50]}...\n" if len(order.load_address) > 50 else f"📍 Откуда: {order.load_address}\n"
                
                if order.unload_address:
                    orders_text += f"📍 Куда: {order.unload_address[:50]}...\n" if len(order.unload_address) > 50 else f"📍 Куда: {order.unload_address}\n"
                
                if order.distance_km:
                    # Убираем .0 для целых чисел
                    distance_str = f"{order.distance_km:.1f}".rstrip('0').rstrip('.')
                    orders_text += f"📏 Расстояние: {distance_str} км\n"
                
                if order.weight_kg:
                    # Убираем .0 для целых чисел
                    weight_str = f"{order.weight_kg:.1f}".rstrip('0').rstrip('.')
                    orders_text += f"⚖️ Вес: {weight_str} кг\n"
                
                if order.price_rub:
                    orders_text += f"💰 Стоимость: {int(order.price_rub)} ₽\n"
                
                orders_text += f"📅 Создан: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                orders_text += "\n"
            
            await message.answer(orders_text)
            
        except Exception as e:
            logger.error(f"Ошибка при получении заказов: {e}")
            await message.answer("❌ Произошла ошибка при получении заказов")

