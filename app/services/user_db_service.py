"""Сервис для работы с пользователями в БД."""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


class UserDBService:
    """Сервис для CRUD операций с пользователями."""

    def __init__(self, session: AsyncSession):
        """Инициализация сервиса с сессией БД."""
        self.session = session

    async def create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None
    ) -> User:
        """Создать нового пользователя."""
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            phone=phone
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_user_by_telegram_id(
        self,
        telegram_id: int
    ) -> Optional[User]:
        """Получить пользователя по telegram_id."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(
        self,
        user_id: int
    ) -> Optional[User]:
        """Получить пользователя по ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> tuple[User, bool]:
        """
        Получить существующего пользователя или создать нового.
        
        Returns:
            tuple[User, bool]: (пользователь, был_ли_создан)
        """
        user = await self.get_user_by_telegram_id(telegram_id)
        
        if user:
            # Обновляем данные если они изменились
            updated = False
            if username and user.username != username:
                user.username = username
                updated = True
            if first_name and user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if last_name and user.last_name != last_name:
                user.last_name = last_name
                updated = True
            
            if updated:
                await self.session.commit()
                await self.session.refresh(user)
            
            return user, False
        
        # Создаём нового пользователя
        user = await self.create_user(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        return user, True

    async def update_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None
    ) -> Optional[User]:
        """Обновить данные пользователя."""
        user = await self.get_user_by_telegram_id(telegram_id)
        
        if not user:
            return None
        
        if username is not None:
            user.username = username
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if phone is not None:
            user.phone = phone
        
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_phone(
        self,
        telegram_id: int,
        phone: str
    ) -> Optional[User]:
        """Обновить номер телефона пользователя."""
        return await self.update_user(
            telegram_id=telegram_id,
            phone=phone
        )

    async def delete_user(
        self,
        telegram_id: int
    ) -> bool:
        """Удалить пользователя."""
        user = await self.get_user_by_telegram_id(telegram_id)
        
        if not user:
            return False
        
        await self.session.delete(user)
        await self.session.commit()
        return True

    async def get_all_users(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> list[User]:
        """Получить список всех пользователей."""
        stmt = select(User).limit(limit).offset(offset).order_by(User.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_users(self) -> int:
        """Получить количество пользователей."""
        from sqlalchemy import func
        stmt = select(func.count(User.id))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def is_manager(self, telegram_id: int) -> bool:
        """Проверить, является ли пользователь менеджером."""
        user = await self.get_user_by_telegram_id(telegram_id)
        return user.is_manager if user else False

    async def set_manager_status(
        self,
        telegram_id: int,
        is_manager: bool
    ) -> Optional[User]:
        """Установить статус менеджера для пользователя."""
        user = await self.get_user_by_telegram_id(telegram_id)
        
        if not user:
            return None
        
        user.is_manager = is_manager
        await self.session.commit()
        await self.session.refresh(user)
        return user

