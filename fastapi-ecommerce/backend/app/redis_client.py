import redis
from backend.app.core.config import settings

# Пример клиента Redis - Используйте новый атрибут REDIS URL
redis_client = redis.Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,  # Автодекодирование ответов
    socket_connect_timeout=5,  # Время ожидания соединения
    socket_keepalive=True  # Подключиться
)

def get_redis():
    return redis_client