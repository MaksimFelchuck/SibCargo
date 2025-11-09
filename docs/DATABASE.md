# База данных SibCargo

## Модели

### User (Пользователь)
Хранит информацию о клиентах бота.

**Поля:**
- `id` — уникальный идентификатор (автоинкремент)
- `telegram_id` — ID пользователя в Telegram (уникальный, индексированный)
- `username` — username в Telegram
- `first_name` — имя
- `last_name` — фамилия
- `phone` — номер телефона
- `created_at` — дата создания
- `updated_at` — дата обновления

**Связи:**
- `orders` — список заказов пользователя (one-to-many)

### Order (Заказ)
Хранит информацию о заказах на грузоперевозку.

**Поля:**
- `id` — уникальный идентификатор (автоинкремент)
- `user_id` — ID пользователя (индексированный)
- `load_date` — дата и время загрузки
- `load_address` — адрес загрузки (текст)
- `load_latitude` — широта точки загрузки
- `load_longitude` — долгота точки загрузки
- `unload_address` — адрес выгрузки (текст)
- `unload_latitude` — широта точки выгрузки
- `unload_longitude` — долгота точки выгрузки
- `weight_kg` — вес груза в килограммах
- `distance_km` — расстояние в километрах
- `price_rub` — стоимость в рублях
- `status` — статус заказа (enum)
- `comment` — комментарий клиента
- `manager_comment` — комментарий менеджера
- `created_at` — дата создания
- `updated_at` — дата обновления

**Статусы заказа (OrderStatus):**
- `DRAFT` — черновик (в процессе оформления)
- `PENDING` — ожидает подтверждения
- `CONFIRMED` — подтверждён менеджером
- `IN_PROGRESS` — в процессе выполнения
- `COMPLETED` — завершён
- `CANCELLED` — отменён

**Связи:**
- `user` — пользователь, создавший заказ (many-to-one)

## Работа с миграциями

### Создание новой миграции
```bash
docker-compose exec bot alembic revision --autogenerate -m "Описание изменений"
```

### Применение миграций
```bash
docker-compose exec bot alembic upgrade head
```

### Откат последней миграции
```bash
docker-compose exec bot alembic downgrade -1
```

### Просмотр истории миграций
```bash
docker-compose exec bot alembic history
```

### Проверка текущей версии
```bash
docker-compose exec bot alembic current
```

## Подключение к БД

### Через psql в контейнере
```bash
docker-compose exec db psql -U sibcargo -d sibcargo
```

### Полезные SQL команды
```sql
-- Список таблиц
\dt

-- Структура таблицы
\d users
\d orders

-- Просмотр данных
SELECT * FROM users;
SELECT * FROM orders;

-- Количество записей
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM orders;
```

## Примеры использования в коде

### Создание сессии
```python
from app.db import get_async_session

async with get_async_session() as session:
    # Работа с БД
    pass
```

### Создание пользователя
```python
from app.db.models import User

user = User(
    telegram_id=123456789,
    username="john_doe",
    first_name="John",
    last_name="Doe"
)
session.add(user)
await session.commit()
```

### Создание заказа
```python
from app.db.models import Order, OrderStatus
from datetime import datetime

order = Order(
    user_id=user.telegram_id,
    load_date=datetime.now(),
    load_address="г. Новосибирск, ул. Ленина, 1",
    load_latitude=55.0084,
    load_longitude=82.9357,
    weight_kg=500.0,
    status=OrderStatus.DRAFT
)
session.add(order)
await session.commit()
```

### Поиск пользователя
```python
from sqlalchemy import select
from app.db.models import User

stmt = select(User).where(User.telegram_id == 123456789)
result = await session.execute(stmt)
user = result.scalar_one_or_none()
```

### Получение заказов пользователя
```python
from sqlalchemy import select
from app.db.models import Order

stmt = select(Order).where(Order.user_id == user.telegram_id)
result = await session.execute(stmt)
orders = result.scalars().all()
```

