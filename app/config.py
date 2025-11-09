"""Конфигурация приложения."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки бота и базы данных."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Telegram
    bot_token: str
    manager_chat_id: int
    
    # Database
    database_url: str = "postgresql+asyncpg://sibcargo:sibcargo@db:5432/sibcargo"
    
    # Pricing (формула: базовая + расстояние * тариф_км + вес * тариф_кг)
    base_price: float = 500.0  # Базовая ставка (руб)
    price_per_km: float = 35.0  # Тариф за километр (руб/км)
    price_per_kg: float = 2.0   # Тариф за килограмм (руб/кг)


settings = Settings()

