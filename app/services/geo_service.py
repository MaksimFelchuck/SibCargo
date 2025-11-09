"""Сервис для работы с геолокацией и расчёта расстояний."""
import logging
from typing import Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

logger = logging.getLogger(__name__)


class GeoService:
    """Сервис для геокодирования и расчёта расстояний."""
    
    def __init__(self):
        """Инициализация геокодера."""
        self.geolocator = Nominatim(user_agent="sibcargo_bot")
    
    async def geocode_address(self, address: str, city: str = "Новосибирск") -> Optional[Tuple[float, float]]:
        """
        Получить координаты по адресу.
        
        Args:
            address: Адрес в текстовом формате
            city: Город по умолчанию (если не указан в адресе)
            
        Returns:
            Кортеж (широта, долгота) или None если адрес не найден
        """
        try:
            # Проверяем, есть ли город в адресе
            address_lower = address.lower()
            cities = ['новосибирск', 'барнаул', 'томск', 'кемерово', 'красноярск', 'омск']
            has_city = any(city_name in address_lower for city_name in cities)
            
            # Если города нет, добавляем по умолчанию
            if not has_city:
                base_address = f"{address} {city}"
            else:
                base_address = address
            
            # Пробуем множество вариантов поиска
            search_variants = [
                # Оригинальный формат
                f"{base_address}, Россия",
                f"{base_address} Россия",
                
                # С "улица" в начале
                f"улица {base_address}, Россия",
                f"улица {base_address} Россия",
                
                # С "ул." в начале
                f"ул. {base_address}, Россия",
                f"ул. {base_address} Россия",
                
                # Если город в начале, пробуем переставить
                # Например: "Новосибирск Сухарная 101" -> "Сухарная 101, Новосибирск, Россия"
            ]
            
            # Если город в начале, пробуем переставить его в конец
            if has_city:
                for city_name in cities:
                    if address_lower.startswith(city_name):
                        # Убираем город из начала
                        street_part = address[len(city_name):].strip().strip(',').strip()
                        if street_part:
                            search_variants.extend([
                                f"{street_part}, {city_name.capitalize()}, Россия",
                                f"улица {street_part}, {city_name.capitalize()}, Россия",
                                f"ул. {street_part}, {city_name.capitalize()}, Россия",
                            ])
                        break
            
            for search_query in search_variants:
                logger.info(f"Попытка поиска: '{search_query}'")
                
                location = self.geolocator.geocode(
                    search_query,
                    timeout=10,
                    exactly_one=True,
                    language='ru'
                )
                
                if location:
                    logger.info(f"✅ Адрес найден: {location.latitude}, {location.longitude}")
                    logger.info(f"Полный адрес: {location.address}")
                    return (location.latitude, location.longitude)
            
            logger.warning(f"❌ Адрес '{address}' не найден ни в одном варианте")
            return None
                
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Ошибка геокодирования адреса '{address}': {e}")
            return None
    
    def calculate_distance(
        self,
        point1: Tuple[float, float],
        point2: Tuple[float, float]
    ) -> float:
        """
        Рассчитать расстояние между двумя точками.
        
        Args:
            point1: Координаты первой точки (широта, долгота)
            point2: Координаты второй точки (широта, долгота)
            
        Returns:
            Расстояние в километрах
        """
        try:
            distance = geodesic(point1, point2).kilometers
            logger.info(f"Расстояние между {point1} и {point2}: {distance:.2f} км")
            return round(distance, 2)
        except Exception as e:
            logger.error(f"Ошибка расчёта расстояния: {e}")
            return 0.0
    
    async def get_address_from_coordinates(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[str]:
        """
        Получить адрес по координатам (обратное геокодирование).
        
        Args:
            latitude: Широта
            longitude: Долгота
            
        Returns:
            Адрес в текстовом формате или None
        """
        try:
            location = self.geolocator.reverse(
                f"{latitude}, {longitude}",
                timeout=10,
                language='ru'
            )
            
            if location:
                logger.info(f"Координаты {latitude}, {longitude} -> {location.address}")
                return location.address
            else:
                return None
                
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Ошибка обратного геокодирования: {e}")
            return None

