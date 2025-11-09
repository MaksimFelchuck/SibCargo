"""Состояния для оформления заказа."""
from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    """Состояния процесса оформления заказа."""
    
    # Выбор даты загрузки
    waiting_for_load_date = State()
    
    # Выбор времени загрузки
    waiting_for_load_time = State()
    
    # Ввод адреса загрузки
    waiting_for_load_address = State()
    
    # Ввод адреса выгрузки
    waiting_for_unload_address = State()
    
    # Ввод веса груза
    waiting_for_weight = State()
    
    # Подтверждение заказа
    waiting_for_confirmation = State()

