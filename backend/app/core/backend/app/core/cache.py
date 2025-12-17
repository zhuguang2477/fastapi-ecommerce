# backend/app/core/cache.py
"""
Redis缓存工具
提供缓存装饰器和缓存管理功能
"""
import json
import functools
import hashlib
import logging
from datetime import timedelta
from typing import Any, Callable, Optional, Union
from fastapi import HTTPException

from backend.app.core.config import settings
from backend.app.redis_client import get_redis

logger = logging.getLogger(__name__)

class CacheService:
    """Сервис кэширования"""
    
    def __init__(self):
        self.redis = get_redis()
        self.default_ttl = 300  # Время кэширования по умолчанию 5 минут
    
    def get_cache_key(self, func_name: str, *args, **kwargs) -> str:
        """Генерация ключа кэша"""
        # Хэширование параметров
        param_str = json.dumps({
            'args': args,
            'kwargs': kwargs
        }, sort_keys=True)
        
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
        
        return f"cache:{func_name}:{param_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Получение данных из кэша"""
        try:
            cached = self.redis.get(key)
            if cached:
                logger.debug(f"Кэш найден: {key}")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Ошибка получения кэша {key}: {e}")
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Запись данных в кэш"""
        try:
            ttl = ttl or self.default_ttl
            json_value = json.dumps(value)
            self.redis.setex(key, ttl, json_value)
            logger.debug(f"Данные записаны в кэш: {key} (TTL: {ttl}с)")
        except Exception as e:
            logger.warning(f"Ошибка записи в кэш {key}: {e}")
    
    async def delete(self, key: str):
        """Удаление данных из кэша"""
        try:
            self.redis.delete(key)
            logger.debug(f"Данные удалены из кэша: {key}")
        except Exception as e:
            logger.warning(f"Ошибка удаления кэша {key}: {e}")
    
    async def clear_pattern(self, pattern: str):
        """Очистка кэша по шаблону"""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
                logger.info(f"Кэш очищен по шаблону: {pattern}, всего ключей: {len(keys)}")
        except Exception as e:
            logger.warning(f"Ошибка очистки кэша по шаблону {pattern}: {e}")


# Глобальный экземпляр сервиса кэширования
cache_service = CacheService()


def cached(
    ttl: int = 300,
    key_prefix: Optional[str] = None,
    ignore_args: bool = False
):
    """
    Декоратор кэширования
    
    Args:
        ttl: Время кэширования в секундах
        key_prefix: Пользовательский префикс ключа кэша
        ignore_args: Игнорировать аргументы (все вызовы используют одинаковый ключ кэша)
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Генерация ключа кэша
            if ignore_args:
                cache_key = f"cache:{key_prefix or func.__name__}:static"
            else:
                # Извлечение shop_id из аргументов
                shop_id = None
                for arg in args:
                    if isinstance(arg, int) and arg > 0:
                        shop_id = arg
                        break
                
                if 'shop_id' in kwargs:
                    shop_id = kwargs['shop_id']
                
                prefix = key_prefix or func.__name__
                if shop_id:
                    cache_key = cache_service.get_cache_key(f"{prefix}:shop_{shop_id}", *args, **kwargs)
                else:
                    cache_key = cache_service.get_cache_key(prefix, *args, **kwargs)
            
            # Попытка получить данные из кэша
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Выполнение функции для получения результата
            result = await func(*args, **kwargs)
            
            # Сохранение результата в кэш
            if result is not None:
                await cache_service.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str = None):
    """
    Декоратор инвалидации кэша
    
    Args:
        pattern: Шаблон ключа кэша, например "cache:get_dashboard_stats:*"
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Очистка кэша после выполнения функции
            if pattern:
                await cache_service.clear_pattern(pattern)
            else:
                # Очистка кэша, связанного с именем функции
                func_name = func.__name__
                await cache_service.clear_pattern(f"cache:{func_name}:*")
            
            return result
        
        return wrapper
    return decorator


# Специальные декораторы для кэширования дашборда
def dashboard_cache(ttl: int = 300):
    """Декоратор кэширования дашборда"""
    return cached(ttl=ttl, key_prefix="dashboard")


def invalidate_dashboard_cache(shop_id: Optional[int] = None):
    """Декоратор инвалидации кэша дашборда"""
    pattern = f"cache:dashboard:*"
    if shop_id:
        pattern = f"cache:dashboard:*shop_{shop_id}*"
    return invalidate_cache(pattern=pattern)


# Быстрая функция для получения сервиса кэширования
def get_cache_service() -> CacheService:
    """Получение экземпляра сервиса кэширования"""
    return cache_service