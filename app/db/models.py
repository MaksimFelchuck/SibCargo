"""Database models."""
from datetime import datetime
from typing import Optional
from enum import Enum as PyEnum

from sqlalchemy import String, BigInteger, Float, DateTime, Text, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class OrderStatus(PyEnum):
    """Статусы заказа."""
    DRAFT = "draft"  # Черновик (в процессе оформления)
    PENDING = "pending"  # Ожидает подтверждения
    CONFIRMED = "confirmed"  # Подтверждён менеджером
    IN_PROGRESS = "in_progress"  # В процессе выполнения
    COMPLETED = "completed"  # Завершён
    CANCELLED = "cancelled"  # Отменён


class User(Base):
    """Модель пользователя (клиента)."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_manager: Mapped[bool] = mapped_column(default=False, nullable=False)
    
    # Метаданные
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Связи
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"


class Order(Base):
    """Модель заказа на грузоперевозку."""
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=False, index=True)
    
    # Дата и время загрузки
    load_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Адрес загрузки
    load_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    load_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    load_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Адрес выгрузки
    unload_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    unload_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unload_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Параметры груза
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Расстояние и стоимость
    distance_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_rub: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Статус заказа
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus),
        default=OrderStatus.DRAFT,
        nullable=False
    )
    
    # Комментарии
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manager_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Метаданные
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Связи
    user: Mapped["User"] = relationship("User", back_populates="orders")

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, user_id={self.user_id}, status={self.status.value})>"

