# backend/app/redis_client.py
import redis
from backend.app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def create_redis_client():
    try:
        redis_url = settings.REDIS_URL
        
        # Разбор URL Redis
        if redis_url.startswith("redis://"):
            # Подключение по URL
            client = redis.Redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                retry_on_timeout=True
            )
        else:
            # Подключение по параметрам
            client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                retry_on_timeout=True
            )
        
        # Тестирование подключения
        client.ping()
        logger.info("✅ Подключение к Redis успешно")
        return client
        
    except redis.ConnectionError as e:
        logger.warning(f"⚠️  Не удалось подключиться к Redis: {e}")
        logger.warning("Приложение продолжит работу, но кэширование недоступно")
        # Возвращаем имитацию Redis клиента, все операции не выполняются
        return MockRedisClient()
    except Exception as e:
        logger.error(f"❌ Ошибка конфигурации Redis: {e}")
        raise

class MockRedisClient:
    """Имитация Redis клиента, используется когда Redis недоступен"""
    def __init__(self):
        self.cache = {}
        logger.info("Используется имитация Redis клиента (без фактического кэширования)")
    
    def get(self, key):
        return self.cache.get(key)
    
    def set(self, key, value, ex=None):
        self.cache[key] = value
        return True
    
    def delete(self, key):
        if key in self.cache:
            del self.cache[key]
        return 1
    
    def keys(self, pattern):
        import re
        pattern = pattern.replace("*", ".*")
        regex = re.compile(pattern)
        return [k for k in self.cache.keys() if regex.match(k)]
    
    def ping(self):
        return "PONG"

# Создание глобального Redis клиента
try:
    redis_client = create_redis_client()
except Exception as e:
    logger.error(f"Не удалось создать Redis клиент: {e}")
    redis_client = MockRedisClient()

def get_redis():
    return redis_client