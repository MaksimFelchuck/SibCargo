# Сервисы для работы с БД

## Обзор

Сервисы предоставляют удобный API для работы с базой данных через SQLAlchemy. Каждый сервис инициализируется с async сессией и предоставляет методы для CRUD операций.

## UserDBService

Сервис для работы с пользователями.

### Инициализация

```python
from app.db import get_async_session
from app.services import UserDBService

async for session in get_async_session():
    user_service = UserDBService(session)
    # Работа с сервисом
```

### Методы

#### create_user
Создать нового пользователя.

```python
user = await user_service.create_user(
    telegram_id=123456789,
    username="john_doe",
    first_name="John",
    last_name="Doe",
    phone="+79991234567"
)
```

#### get_user_by_telegram_id
Получить пользователя по Telegram ID.

```python
user = await user_service.get_user_by_telegram_id(telegram_id=123456789)
```

#### get_or_create_user
Получить существующего пользователя или создать нового. Автоматически обновляет данные если они изменились.

```python
user, created = await user_service.get_or_create_user(
    telegram_id=123456789,
    username="john_doe",
    first_name="John",
    last_name="Doe"
)

if created:
    print("Новый пользователь создан")
else:
    print("Пользователь уже существует")
```

#### update_user
Обновить данные пользователя.

```python
user = await user_service.update_user(
    telegram_id=123456789,
    username="new_username",
    phone="+79991234567"
)
```

#### update_phone
Обновить только номер телефона.

```python
user = await user_service.update_phone(
    telegram_id=123456789,
    phone="+79991234567"
)
```

#### delete_user
Удалить пользователя.

```python
success = await user_service.delete_user(telegram_id=123456789)
```

#### get_all_users
Получить список всех пользователей с пагинацией.

```python
users = await user_service.get_all_users(limit=50, offset=0)
```

#### count_users
Получить общее количество пользователей.

```python
total = await user_service.count_users()
```

---

## OrderDBService

Сервис для работы с заказами.

### Инициализация

```python
from app.db import get_async_session
from app.services import OrderDBService

async for session in get_async_session():
    order_service = OrderDBService(session)
    # Работа с сервисом
```

### Методы

#### create_order
Создать новый заказ.

```python
from datetime import datetime
from app.db.models import OrderStatus

order = await order_service.create_order(
    user_id=123456789,
    load_date=datetime.now(),
    load_address="г. Новосибирск, ул. Ленина, 1",
    load_latitude=55.0084,
    load_longitude=82.9357,
    unload_address="г. Новосибирск, ул. Красный проспект, 1",
    unload_latitude=55.0415,
    unload_longitude=82.9346,
    weight_kg=500.0,
    distance_km=5.2,
    price_rub=1200.0,
    status=OrderStatus.DRAFT,
    comment="Хрупкий груз"
)
```

#### get_order_by_id
Получить заказ по ID.

```python
order = await order_service.get_order_by_id(order_id=1)
```

#### get_user_orders
Получить все заказы пользователя.

```python
orders = await order_service.get_user_orders(
    user_id=123456789,
    limit=10,
    offset=0
)
```

#### get_user_orders_by_status
Получить заказы пользователя по статусу.

```python
from app.db.models import OrderStatus

pending_orders = await order_service.get_user_orders_by_status(
    user_id=123456789,
    status=OrderStatus.PENDING,
    limit=10
)
```

#### get_orders_by_status
Получить все заказы по статусу.

```python
from app.db.models import OrderStatus

all_pending = await order_service.get_orders_by_status(
    status=OrderStatus.PENDING,
    limit=100,
    offset=0
)
```

#### update_order
Обновить заказ (любые поля).

```python
order = await order_service.update_order(
    order_id=1,
    weight_kg=600.0,
    price_rub=1400.0,
    comment="Обновлённый комментарий"
)
```

#### update_order_status
Обновить статус заказа.

```python
from app.db.models import OrderStatus

order = await order_service.update_order_status(
    order_id=1,
    status=OrderStatus.CONFIRMED,
    manager_comment="Заказ подтверждён, водитель выезжает"
)
```

#### calculate_and_update_price
Рассчитать и обновить стоимость заказа по формуле.

```python
order = await order_service.calculate_and_update_price(
    order_id=1,
    base_price=600.0,
    price_per_km=20.0,
    price_per_kg=1.0
)
# Формула: price = 600 + (distance_km * 20) + (weight_kg * 1)
```

#### get_user_draft_order
Получить черновик заказа пользователя (если есть).

```python
draft = await order_service.get_user_draft_order(user_id=123456789)
```

#### get_or_create_draft_order
Получить существующий черновик или создать новый.

```python
draft, created = await order_service.get_or_create_draft_order(user_id=123456789)
```

#### delete_order
Удалить заказ.

```python
success = await order_service.delete_order(order_id=1)
```

#### count_orders
Получить количество заказов с фильтрами.

```python
from app.db.models import OrderStatus

# Все заказы пользователя
total = await order_service.count_orders(user_id=123456789)

# Все заказы со статусом PENDING
pending_count = await order_service.count_orders(status=OrderStatus.PENDING)

# Все заказы
all_count = await order_service.count_orders()
```

---

## Пример использования в хендлере

```python
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart

from app.db import get_async_session
from app.services import UserDBService, OrderDBService

router = Router()

@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    """Обработчик команды /start."""
    async for session in get_async_session():
        # Создаём сервисы
        user_service = UserDBService(session)
        order_service = OrderDBService(session)
        
        # Получаем или создаём пользователя
        user, created = await user_service.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        
        # Получаем количество заказов пользователя
        orders_count = await order_service.count_orders(user_id=user.telegram_id)
        
        await message.answer(
            f"Привет, {user.first_name}!\n"
            f"У вас {orders_count} заказов."
        )
```

---

## Статусы заказов (OrderStatus)

```python
from app.db.models import OrderStatus

OrderStatus.DRAFT          # Черновик (в процессе оформления)
OrderStatus.PENDING        # Ожидает подтверждения
OrderStatus.CONFIRMED      # Подтверждён менеджером
OrderStatus.IN_PROGRESS    # В процессе выполнения
OrderStatus.COMPLETED      # Завершён
OrderStatus.CANCELLED      # Отменён
```

---

## Best Practices

1. **Всегда используйте async for** для получения сессии:
   ```python
   async for session in get_async_session():
       service = UserDBService(session)
       # работа с сервисом
   ```

2. **Обрабатывайте исключения**:
   ```python
   try:
       user = await user_service.create_user(...)
   except Exception as e:
       logger.error(f"Ошибка: {e}")
   ```

3. **Используйте get_or_create** для пользователей:
   ```python
   user, created = await user_service.get_or_create_user(...)
   ```

4. **Проверяйте результаты**:
   ```python
   user = await user_service.get_user_by_telegram_id(123)
   if not user:
       # Обработка отсутствия пользователя
       return
   ```

