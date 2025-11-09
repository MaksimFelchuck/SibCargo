# Примеры SQL запросов для SibCargo

## Подключение к БД
```bash
docker-compose exec db psql -U sibcargo -d sibcargo
```

## Пользователи

### Просмотр всех пользователей
```sql
SELECT id, telegram_id, username, first_name, last_name, created_at 
FROM users 
ORDER BY created_at DESC;
```

### Поиск пользователя по telegram_id
```sql
SELECT * FROM users WHERE telegram_id = 123456789;
```

### Количество пользователей
```sql
SELECT COUNT(*) as total_users FROM users;
```

### Пользователи с заказами
```sql
SELECT u.telegram_id, u.username, COUNT(o.id) as orders_count
FROM users u
LEFT JOIN orders o ON u.telegram_id = o.user_id
GROUP BY u.id, u.telegram_id, u.username
ORDER BY orders_count DESC;
```

## Заказы

### Просмотр всех заказов
```sql
SELECT id, user_id, load_address, unload_address, weight_kg, price_rub, status, created_at
FROM orders
ORDER BY created_at DESC;
```

### Заказы по статусу
```sql
SELECT * FROM orders WHERE status = 'PENDING';
```

### Заказы пользователя
```sql
SELECT o.id, o.load_address, o.unload_address, o.price_rub, o.status, o.created_at
FROM orders o
WHERE o.user_id = 123456789
ORDER BY o.created_at DESC;
```

### Статистика по статусам
```sql
SELECT status, COUNT(*) as count
FROM orders
GROUP BY status
ORDER BY count DESC;
```

### Средняя стоимость заказа
```sql
SELECT 
    AVG(price_rub) as avg_price,
    MIN(price_rub) as min_price,
    MAX(price_rub) as max_price
FROM orders
WHERE price_rub IS NOT NULL;
```

### Заказы за последние 7 дней
```sql
SELECT COUNT(*) as orders_last_week
FROM orders
WHERE created_at >= NOW() - INTERVAL '7 days';
```

### Самые активные пользователи
```sql
SELECT u.username, u.first_name, COUNT(o.id) as total_orders
FROM users u
INNER JOIN orders o ON u.telegram_id = o.user_id
GROUP BY u.id, u.username, u.first_name
ORDER BY total_orders DESC
LIMIT 10;
```

### Общая выручка
```sql
SELECT 
    SUM(price_rub) as total_revenue,
    COUNT(*) as completed_orders
FROM orders
WHERE status = 'COMPLETED' AND price_rub IS NOT NULL;
```

## Обновление данных

### Изменить статус заказа
```sql
UPDATE orders 
SET status = 'CONFIRMED', updated_at = NOW()
WHERE id = 1;
```

### Добавить комментарий менеджера
```sql
UPDATE orders 
SET manager_comment = 'Заказ подтверждён, водитель выезжает', updated_at = NOW()
WHERE id = 1;
```

### Обновить телефон пользователя
```sql
UPDATE users 
SET phone = '+79991234567', updated_at = NOW()
WHERE telegram_id = 123456789;
```

## Удаление данных

### Удалить черновики старше 30 дней
```sql
DELETE FROM orders 
WHERE status = 'DRAFT' 
AND created_at < NOW() - INTERVAL '30 days';
```

### Удалить пользователя и его заказы
```sql
-- Сначала удаляем заказы
DELETE FROM orders WHERE user_id = 123456789;

-- Затем пользователя
DELETE FROM users WHERE telegram_id = 123456789;
```

## Аналитика

### Заказы по дням за последний месяц
```sql
SELECT 
    DATE(created_at) as order_date,
    COUNT(*) as orders_count,
    SUM(price_rub) as daily_revenue
FROM orders
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY order_date DESC;
```

### Средний вес груза по статусам
```sql
SELECT 
    status,
    AVG(weight_kg) as avg_weight,
    COUNT(*) as count
FROM orders
WHERE weight_kg IS NOT NULL
GROUP BY status;
```

### Популярные адреса загрузки
```sql
SELECT 
    load_address,
    COUNT(*) as times_used
FROM orders
WHERE load_address IS NOT NULL
GROUP BY load_address
ORDER BY times_used DESC
LIMIT 10;
```

## Полезные команды psql

```sql
-- Список таблиц
\dt

-- Структура таблицы
\d users
\d orders

-- Список индексов
\di

-- Размер таблиц
\dt+

-- Выход
\q
```

