from fastapi import APIRouter, Depends
from sqlalchemy import text
from datetime import datetime
import pytz

from backend.app.schemas.health import (
    HealthCheckResponse, 
    DatabaseHealthResponse, 
    RedisHealthResponse
)
from backend.app.database import get_db
from backend.app.redis_client import get_redis
from backend.app.core.config import settings
from sqlalchemy.orm import Session
import redis

router = APIRouter()


def check_database_health(db: Session) -> bool:
    """检查数据库连接状态"""
    try:
        # Выполнить простой запрос для проверки подключения к базе данных
        db.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database health check failed: {e}")
        return False


def check_redis_health(redis_client: redis.Redis) -> bool:
    """Проверьте состояние соединения Redis"""
    try:
        return redis_client.ping()
    except Exception as e:
        print(f"Redis health check failed: {e}")
        return False


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Применение проверки состояния здоровья",
    description="Проверка состояния подключения приложений, баз данных и Redis"
)
async def health_check(
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Комплексный медицинский осмотр"""
    # Проверка подключения к базе данных
    db_healthy = check_database_health(db)
    
    # Проверьте соединение Redis
    redis_healthy = check_redis_health(redis_client)
    
    # Определение общего состояния
    overall_status = "healthy" if (db_healthy and redis_healthy) else "unhealthy"
    
    # Получение текущей метки времени
    current_time = datetime.now(pytz.utc).isoformat()
    
    return HealthCheckResponse(
        status=overall_status,
        database="healthy" if db_healthy else "unhealthy",
        redis="healthy" if redis_healthy else "unhealthy",
        timestamp=current_time,
        version=settings.VERSION
    )


@router.get(
    "/health/database",
    response_model=DatabaseHealthResponse,
    summary="База данных медицинский осмотр",
    description="Проверьте состояние подключения к базе данных отдельно"
)
async def database_health_check(db: Session = Depends(get_db)):
    """База данных для проверки здоровья"""
    is_healthy = check_database_health(db)
    
    return DatabaseHealthResponse(
        status="connected" if is_healthy else "disconnected"
    )


@router.get(
    "/health/redis", 
    response_model=RedisHealthResponse,
    summary="Redis Медицинский осмотр",
    description="Проверьте состояние соединения Redis."
)
async def redis_health_check(redis_client: redis.Redis = Depends(get_redis)):
    """Проверка здоровья Redis"""
    is_healthy = check_redis_health(redis_client)
    
    return RedisHealthResponse(
        status="connected" if is_healthy else "disconnected"
    )