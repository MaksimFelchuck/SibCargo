"""Database configuration and session management."""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


# Создание async engine
engine = create_async_engine(
    settings.database_url,
    echo=True,  # Логирование SQL запросов (для разработки)
    future=True
)

# Создание фабрики сессий
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для получения async сессии БД."""
    async with async_session_maker() as session:
        yield session

