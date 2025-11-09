"""Сервис для работы с заказами в БД."""
from typing import Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Order, OrderStatus


class OrderDBService:
    """Сервис для CRUD операций с заказами."""

    def __init__(self, session: AsyncSession):
        """Инициализация сервиса с сессией БД."""
        self.session = session

    async def create_order(
        self,
        user_id: int,
        load_date: Optional[datetime] = None,
        load_address: Optional[str] = None,
        load_latitude: Optional[float] = None,
        load_longitude: Optional[float] = None,
        unload_address: Optional[str] = None,
        unload_latitude: Optional[float] = None,
        unload_longitude: Optional[float] = None,
        weight_kg: Optional[float] = None,
        distance_km: Optional[float] = None,
        price_rub: Optional[float] = None,
        status: OrderStatus = OrderStatus.DRAFT,
        comment: Optional[str] = None
    ) -> Order:
        """Создать новый заказ."""
        order = Order(
            user_id=user_id,
            load_date=load_date,
            load_address=load_address,
            load_latitude=load_latitude,
            load_longitude=load_longitude,
            unload_address=unload_address,
            unload_latitude=unload_latitude,
            unload_longitude=unload_longitude,
            weight_kg=weight_kg,
            distance_km=distance_km,
            price_rub=price_rub,
            status=status,
            comment=comment
        )
        self.session.add(order)
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def get_order_by_id(
        self,
        order_id: int
    ) -> Optional[Order]:
        """Получить заказ по ID."""
        stmt = select(Order).where(Order.id == order_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_orders(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> list[Order]:
        """Получить все заказы пользователя."""
        stmt = (
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_orders_by_status(
        self,
        user_id: int,
        status: OrderStatus,
        limit: int = 50
    ) -> list[Order]:
        """Получить заказы пользователя по статусу."""
        stmt = (
            select(Order)
            .where(Order.user_id == user_id, Order.status == status)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_orders_by_status(
        self,
        status: OrderStatus,
        limit: int = 100,
        offset: int = 0
    ) -> list[Order]:
        """Получить все заказы по статусу."""
        stmt = (
            select(Order)
            .where(Order.status == status)
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_order(
        self,
        order_id: int,
        **kwargs
    ) -> Optional[Order]:
        """
        Обновить заказ.
        
        Args:
            order_id: ID заказа
            **kwargs: Поля для обновления (load_date, load_address, weight_kg, и т.д.)
        """
        order = await self.get_order_by_id(order_id)
        
        if not order:
            return None
        
        # Обновляем только переданные поля
        for key, value in kwargs.items():
            if hasattr(order, key) and value is not None:
                setattr(order, key, value)
        
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def update_order_status(
        self,
        order_id: int,
        status: OrderStatus,
        manager_comment: Optional[str] = None
    ) -> Optional[Order]:
        """Обновить статус заказа."""
        order = await self.get_order_by_id(order_id)
        
        if not order:
            return None
        
        order.status = status
        if manager_comment:
            order.manager_comment = manager_comment
        
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def calculate_and_update_price(
        self,
        order_id: int,
        base_price: float,
        price_per_km: float,
        price_per_kg: float
    ) -> Optional[Order]:
        """
        Рассчитать и обновить стоимость заказа.
        
        Формула: price = base_price + (distance_km * price_per_km) + (weight_kg * price_per_kg)
        """
        order = await self.get_order_by_id(order_id)
        
        if not order:
            return None
        
        # Расчёт стоимости
        distance_cost = (order.distance_km or 0) * price_per_km
        weight_cost = (order.weight_kg or 0) * price_per_kg
        total_price = base_price + distance_cost + weight_cost
        
        order.price_rub = round(total_price, 2)
        
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def delete_order(
        self,
        order_id: int
    ) -> bool:
        """Удалить заказ."""
        order = await self.get_order_by_id(order_id)
        
        if not order:
            return False
        
        await self.session.delete(order)
        await self.session.commit()
        return True

    async def get_all_orders(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> list[Order]:
        """Получить список всех заказов."""
        stmt = select(Order).limit(limit).offset(offset).order_by(Order.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_orders(
        self,
        user_id: Optional[int] = None,
        status: Optional[OrderStatus] = None
    ) -> int:
        """Получить количество заказов с фильтрами."""
        from sqlalchemy import func
        
        stmt = select(func.count(Order.id))
        
        if user_id:
            stmt = stmt.where(Order.user_id == user_id)
        if status:
            stmt = stmt.where(Order.status == status)
        
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_user_draft_order(
        self,
        user_id: int
    ) -> Optional[Order]:
        """Получить черновик заказа пользователя (если есть)."""
        stmt = (
            select(Order)
            .where(Order.user_id == user_id, Order.status == OrderStatus.DRAFT)
            .order_by(Order.updated_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create_draft_order(
        self,
        user_id: int
    ) -> tuple[Order, bool]:
        """
        Получить существующий черновик или создать новый.
        
        Returns:
            tuple[Order, bool]: (заказ, был_ли_создан)
        """
        draft = await self.get_user_draft_order(user_id)
        
        if draft:
            return draft, False
        
        # Создаём новый черновик
        order = await self.create_order(
            user_id=user_id,
            status=OrderStatus.DRAFT
        )
        return order, True
