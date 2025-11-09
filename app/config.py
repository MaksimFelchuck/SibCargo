"""Конфигурация приложения."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки бота и базы данных."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False  # Игнорируем регистр
    )
    
    # Telegram
    bot_token: str = Field(alias="BOT_TOKEN")
    manager_chat_id: int = Field(alias="MANAGER_CHAT_ID")
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://sibcargo:sibcargo@db:5432/sibcargo",
        alias="DATABASE_URL"
    )
    
    # Pricing (формула: базовая + расстояние * тариф_км + вес * тариф_кг)
    base_price: float = Field(default=500.0, alias="BASE_PRICE")  # Базовая ставка (руб)
    price_per_km: float = Field(default=35.0, alias="PRICE_PER_KM")  # Тариф за километр (руб/км)
    price_per_kg: float = Field(default=2.0, alias="PRICE_PER_KG")  # Тариф за килограмм (руб/кг)


settings = Settings()

