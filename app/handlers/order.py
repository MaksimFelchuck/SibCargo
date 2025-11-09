"""Обработчики для оформления заказа."""
import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback, get_user_locale

from app.states.order import OrderStates
from app.keyboards.order import (
    get_cancel_keyboard,
    get_date_keyboard,
    get_time_keyboard,
    get_location_keyboard,
    get_confirmation_keyboard
)
from app.db import get_async_session
from app.services import UserDBService, OrderDBService, GeoService
from app.config import settings

order_router = Router()
logger = logging.getLogger(__name__)

# Настраиваем календарь с русскими текстами
calendar = SimpleCalendar(
    locale='ru_RU.UTF-8',
    show_alerts=True,
    cancel_btn='Отмена',
    today_btn='Сегодня'
)


@order_router.message(F.text == "🚚 Оформить перевозку")
async def start_order(message: Message, state: FSMContext) -> None:
    """Начало оформления заказа."""
    await state.clear()  # Очищаем предыдущее состояние
    
    await message.answer(
        "🚚 <b>Оформление заказа на перевозку</b>\n\n"
        "Давайте начнём! Я задам вам несколько вопросов.\n\n"
        "📅 <b>Шаг 1 из 5: Дата загрузки</b>\n"
        "Выберите дату, когда нужно забрать груз:",
        reply_markup=await get_date_keyboard()
    )
    await state.set_state(OrderStates.waiting_for_load_date)


@order_router.callback_query(StateFilter(OrderStates.waiting_for_load_date), SimpleCalendarCallback.filter())
async def process_load_date(callback: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext) -> None:
    """Обработка выбора даты загрузки через календарь."""
    selected, date = await calendar.process_selection(callback, callback_data)
    
    if selected:
        # Проверяем, что дата не в прошлом
        if date.date() < datetime.now().date():
            await callback.answer("❌ Нельзя выбрать прошедшую дату", show_alert=True)
            return
        
        # Сохраняем дату
        await state.update_data(load_date=date.strftime("%Y-%m-%d"))
        
        await callback.message.edit_text(
            f"✅ Дата загрузки: <b>{date.strftime('%d.%m.%Y')}</b>\n\n"
            f"⏰ <b>Шаг 2 из 5: Время загрузки</b>\n"
            f"Выберите удобное время:",
            reply_markup=get_time_keyboard()
        )
        await state.set_state(OrderStates.waiting_for_load_time)
        await callback.answer()


@order_router.callback_query(StateFilter(OrderStates.waiting_for_load_time), F.data.startswith("time_"))
async def process_load_time(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора времени загрузки."""
    time_str = callback.data.split("_")[1]  # time_10:00
    
    # Получаем сохранённую дату
    data = await state.get_data()
    date_str = data.get("load_date")
    
    # Объединяем дату и время
    load_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    
    await state.update_data(load_datetime=load_datetime.isoformat())
    
    await callback.message.edit_text(
        f"✅ Дата и время: <b>{load_datetime.strftime('%d.%m.%Y %H:%M')}</b>\n\n"
        f"📍 <b>Шаг 3 из 5: Адрес загрузки</b>\n"
        f"Откуда нужно забрать груз?"
    )
    await callback.message.answer(
        "<b>⚠️ ВАЖНО: Укажите город и улицу с номером дома!</b>\n\n"
        "<b>✅ Примеры правильного ввода:</b>\n"
        "  • <code>Новосибирск улица Ленина 1</code>\n"
        "  • <code>Барнаул Ленина 10</code>\n"
        "  • <code>Томск Кирова 50</code>\n"
        "  • <code>Кемерово Весенняя 20</code>",
        reply_markup=get_location_keyboard()
    )
    await state.set_state(OrderStates.waiting_for_load_address)
    await callback.answer()


@order_router.message(StateFilter(OrderStates.waiting_for_load_address), F.text)
async def process_load_address_text(message: Message, state: FSMContext) -> None:
    """Обработка адреса загрузки (текст)."""
    if message.text == "❌ Отменить":
        await cancel_order(message, state)
        return
    
    # Геокодируем адрес (город должен быть в тексте)
    geo_service = GeoService()
    processing_msg = await message.answer("🔍 Ищу адрес на карте...")
    
    # Используем Новосибирск по умолчанию, если город не указан
    coordinates = await geo_service.geocode_address(message.text, city="Новосибирск")
    
    if coordinates:
        await state.update_data(
            load_address=message.text,
            load_latitude=coordinates[0],
            load_longitude=coordinates[1]
        )
        
        await processing_msg.delete()
        await message.answer(
            f"✅ Адрес загрузки: <b>{message.text}</b>\n\n"
            f"📍 <b>Шаг 4 из 5: Адрес выгрузки</b>\n"
            f"Куда нужно доставить груз?\n\n"
            f"<b>✅ Примеры:</b>\n"
            f"  • <code>Барнаул Ленина 10</code>\n"
            f"  • <code>Томск Кирова 50</code>\n"
            f"  • <code>Кемерово Весенняя 20</code>",
            reply_markup=get_location_keyboard()
        )
        await state.set_state(OrderStates.waiting_for_unload_address)
    else:
        await processing_msg.delete()
        await message.answer(
            f"❌ Не удалось найти адрес: <b>{message.text}</b>\n\n"
            f"💡 <b>Советы для точного поиска:</b>\n"
            f"• Укажите улицу полностью: «улица Кирова 10» или «Кирова 10»\n"
            f"• Для дробных номеров: «Островского 195/3»\n"
            f"• Если не находит, попробуйте без дроби: «Островского 195»\n"
            f"• Или укажите город: «Новосибирск, Кирова 10»\n\n"
            f"Или выберите точку на карте (нажмите на мою точку выше ☝️)",
            reply_markup=get_location_keyboard()
        )


# TODO: Добавить поддержку геолокации позже
# @order_router.message(StateFilter(OrderStates.waiting_for_load_address), F.location)
# async def process_load_location(message: Message, state: FSMContext) -> None:
#     """Обработка геолокации загрузки."""
#     location = message.location
#     
#     # Получаем адрес по координатам
#     geo_service = GeoService()
#     processing_msg = await message.answer("🔍 Определяю адрес...")
#     
#     address = await geo_service.get_address_from_coordinates(
#         location.latitude,
#         location.longitude
#     )
#     
#     if address:
#         display_address = address
#     else:
#         display_address = f"Координаты: {location.latitude:.6f}, {location.longitude:.6f}"
#     
#     await state.update_data(
#         load_address=display_address,
#         load_latitude=location.latitude,
#         load_longitude=location.longitude
#     )
#     
#     await processing_msg.delete()
#     await message.answer(
#         f"✅ Адрес загрузки: <b>{display_address}</b>\n\n"
#         f"📍 <b>Шаг 4 из 5: Адрес выгрузки</b>\n"
#         f"Куда нужно доставить груз?\n\n"
#         f"<b>✅ Примеры:</b>\n"
#         f"  • <code>Барнаул Ленина 10</code>\n"
#         f"  • <code>Томск Кирова 50</code>\n"
#         f"  • <code>Кемерово Весенняя 20</code>",
#         reply_markup=get_location_keyboard()
#     )
#     await state.set_state(OrderStates.waiting_for_unload_address)


@order_router.message(StateFilter(OrderStates.waiting_for_unload_address), F.text)
async def process_unload_address_text(message: Message, state: FSMContext) -> None:
    """Обработка адреса выгрузки (текст)."""
    if message.text == "❌ Отменить":
        await cancel_order(message, state)
        return
    
    # Геокодируем адрес (город должен быть в тексте)
    geo_service = GeoService()
    processing_msg = await message.answer("🔍 Ищу адрес на карте...")
    
    # Используем Новосибирск по умолчанию, если город не указан
    coordinates = await geo_service.geocode_address(message.text, city="Новосибирск")
    
    if coordinates:
        await state.update_data(
            unload_address=message.text,
            unload_latitude=coordinates[0],
            unload_longitude=coordinates[1]
        )
        
        await processing_msg.delete()
        await message.answer(
            f"✅ Адрес выгрузки: <b>{message.text}</b>\n"
            f"📍 Координаты: {coordinates[0]:.6f}, {coordinates[1]:.6f}\n\n"
            f"⚖️ <b>Шаг 5 из 5: Вес груза</b>\n"
            f"Укажите вес груза в килограммах (например: 500):",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(OrderStates.waiting_for_weight)
    else:
        await processing_msg.delete()
        await message.answer(
            f"❌ Не удалось найти адрес: <b>{message.text}</b>\n\n"
            f"💡 <b>Советы для точного поиска:</b>\n"
            f"• Укажите улицу полностью: «улица Кирова 10» или «Кирова 10»\n"
            f"• Для дробных номеров: «Островского 195/3»\n"
            f"• Если не находит, попробуйте без дроби: «Островского 195»\n"
            f"• Или укажите город: «Новосибирск, Кирова 10»\n\n"
            f"Или выберите точку на карте (нажмите на мою точку выше ☝️)",
            reply_markup=get_location_keyboard()
        )


# TODO: Добавить поддержку геолокации позже
# @order_router.message(StateFilter(OrderStates.waiting_for_unload_address), F.location)
# async def process_unload_location(message: Message, state: FSMContext) -> None:
#     """Обработка геолокации выгрузки."""
#     location = message.location
#     
#     # Получаем адрес по координатам
#     geo_service = GeoService()
#     processing_msg = await message.answer("🔍 Определяю адрес...")
#     
#     address = await geo_service.get_address_from_coordinates(
#         location.latitude,
#         location.longitude
#     )
#     
#     if address:
#         display_address = address
#     else:
#         display_address = f"Координаты: {location.latitude:.6f}, {location.longitude:.6f}"
#     
#     await state.update_data(
#         unload_address=display_address,
#         unload_latitude=location.latitude,
#         unload_longitude=location.longitude
#     )
#     
#     await processing_msg.delete()
#     await message.answer(
#         f"✅ Адрес выгрузки: <b>{display_address}</b>\n\n"
#         f"⚖️ <b>Шаг 5 из 5: Вес груза</b>\n"
#         f"Укажите вес груза в килограммах (например: 500):",
#         reply_markup=get_cancel_keyboard()
#     )
#     await state.set_state(OrderStates.waiting_for_weight)


@order_router.message(StateFilter(OrderStates.waiting_for_weight), F.text)
async def process_weight(message: Message, state: FSMContext) -> None:
    """Обработка веса груза."""
    if message.text == "❌ Отменить":
        await cancel_order(message, state)
        return
    
    try:
        weight = float(message.text.replace(",", "."))
        
        if weight <= 0:
            await message.answer("❌ Вес должен быть больше 0. Попробуйте ещё раз:")
            return
        
        if weight > 10000:
            await message.answer("❌ Вес слишком большой. Максимум 10000 кг. Попробуйте ещё раз:")
            return
        
        await state.update_data(weight_kg=weight)
        
        # Получаем все данные
        data = await state.get_data()
        
        # Расчёт реального расстояния
        geo_service = GeoService()
        
        load_lat = data.get("load_latitude")
        load_lon = data.get("load_longitude")
        unload_lat = data.get("unload_latitude")
        unload_lon = data.get("unload_longitude")
        
        if load_lat and load_lon and unload_lat and unload_lon:
            distance_km = geo_service.calculate_distance(
                (load_lat, load_lon),
                (unload_lat, unload_lon)
            )
        else:
            # Если координат нет, используем минимальное расстояние
            distance_km = 5.0
            logger.warning("Координаты не найдены, используется минимальное расстояние")
        
        # Расчёт стоимости (округляем до целого числа)
        price = round(settings.base_price + (distance_km * settings.price_per_km) + (weight * settings.price_per_kg))
        
        await state.update_data(distance_km=distance_km, price_rub=price)
        
        # Формируем сводку
        load_dt = datetime.fromisoformat(data["load_datetime"])
        
        # Убираем .0 для целых чисел
        distance_str = f"{distance_km:.1f}".rstrip('0').rstrip('.')
        weight_str = f"{weight:.1f}".rstrip('0').rstrip('.')
        
        summary = (
            f"📋 <b>Проверьте данные заказа:</b>\n\n"
            f"📅 Дата и время: <b>{load_dt.strftime('%d.%m.%Y %H:%M')}</b>\n"
            f"📍 Откуда: <b>{data['load_address']}</b>\n"
            f"📍 Куда: <b>{data['unload_address']}</b>\n"
            f"📏 Расстояние: <b>{distance_str} км</b>\n"
            f"⚖️ Вес: <b>{weight_str} кг</b>\n\n"
            f"💰 <b>Примерная стоимость: {int(price)} ₽</b>\n\n"
            f"Подтверждаете заказ?"
        )
        
        await message.answer(summary, reply_markup=get_confirmation_keyboard())
        await state.set_state(OrderStates.waiting_for_confirmation)
        
    except ValueError:
        await message.answer("❌ Неверный формат. Введите число (например: 500):")


@order_router.callback_query(StateFilter(OrderStates.waiting_for_confirmation), F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext) -> None:
    """Подтверждение и сохранение заказа."""
    data = await state.get_data()
    
    async for session in get_async_session():
        try:
            # Получаем пользователя
            user_service = UserDBService(session)
            user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            
            if not user:
                await callback.answer("❌ Ошибка: пользователь не найден", show_alert=True)
                return
            
            # Создаём заказ
            order_service = OrderDBService(session)
            load_datetime = datetime.fromisoformat(data["load_datetime"])
            
            from app.db.models import OrderStatus
            order = await order_service.create_order(
                user_id=user.telegram_id,
                load_date=load_datetime,
                load_address=data["load_address"],
                load_latitude=data.get("load_latitude"),
                load_longitude=data.get("load_longitude"),
                unload_address=data["unload_address"],
                unload_latitude=data.get("unload_latitude"),
                unload_longitude=data.get("unload_longitude"),
                weight_kg=data["weight_kg"],
                distance_km=data.get("distance_km"),
                price_rub=data.get("price_rub"),
                status=OrderStatus.PENDING
            )
            
            await callback.message.edit_text(
                f"✅ <b>Заказ #{order.id} успешно создан!</b>\n\n"
                f"Наш менеджер свяжется с вами в ближайшее время для подтверждения.\n\n"
                f"Вы можете посмотреть свои заказы в разделе «📦 Мои заказы»"
            )
            
            # Возвращаем главное меню
            from app.keyboards.main_menu import get_main_menu
            await callback.message.answer(
                "Выберите действие:",
                reply_markup=get_main_menu()
            )
            
            # TODO: Отправить уведомление менеджеру
            
            await state.clear()
            await callback.answer("✅ Заказ создан!")
            
            logger.info(f"Создан заказ #{order.id} от пользователя {user.telegram_id}")
            
        except Exception as e:
            logger.error(f"Ошибка при создании заказа: {e}")
            await callback.answer("❌ Произошла ошибка при создании заказа", show_alert=True)


@order_router.callback_query(StateFilter(OrderStates.waiting_for_confirmation), F.data == "cancel_order")
async def cancel_order_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Отмена заказа через callback."""
    from app.keyboards.main_menu import get_main_menu
    
    await callback.message.edit_text("❌ Заказ отменён")
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=get_main_menu()
    )
    await state.clear()
    await callback.answer()


async def cancel_order(message: Message, state: FSMContext) -> None:
    """Отмена оформления заказа."""
    from app.keyboards.main_menu import get_main_menu
    
    await message.answer(
        "❌ Оформление заказа отменено",
        reply_markup=get_main_menu()
    )
    await state.clear()


@order_router.message(F.text == "❌ Отменить")
async def cancel_order_button(message: Message, state: FSMContext) -> None:
    """Обработка кнопки отмены."""
    await cancel_order(message, state)

