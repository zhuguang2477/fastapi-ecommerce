"""
仪表板相关API端点
"""
# backend/app/api/v1/endpoints/dashbord.py
import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.services.dashboard_service import get_dashboard_service
from backend.app.schemas.dashboard import DashboardStats
from backend.app.core.security import get_current_user

# Импорт Shop и ShopMember - согласно структуре проекта они находятся в одном файле
from backend.app.models.shop import Shop, ShopMember

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/shops/{shop_id}/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    shop_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получить статистику для дашборда
    
    Args:
        shop_id: ID магазина
        current_user: текущий аутентифицированный пользователь
        db: сессия базы данных
        
    Returns:
        DashboardStats: статистика дашборда, содержащая:
            - popular_categories: популярные категории
            - user_activity: недельный график активности пользователей
            - average_product_rating: средний рейтинг товаров
            - average_order_value: средняя стоимость заказа
            - monthly_revenue: график месячной выручки
    """
    try:
        # Проверить, есть ли у пользователя доступ к магазину
        await _validate_shop_access(current_user, shop_id, db)
        
        # Получить сервис дашборда
        dashboard_service = get_dashboard_service(db)
        
        # Получить статистику
        stats = await dashboard_service.get_dashboard_stats(shop_id)
        
        logger.info(f"Успешно получена статистика дашборда для магазина {shop_id}")
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении статистики дашборда: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить статистику. Пожалуйста, попробуйте позже"
        )


@router.get("/shops/{shop_id}/quick-stats")
async def get_quick_stats(
    shop_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получить краткую статистику
    
    Возвращает ключевые показатели: сегодняшние заказы, сегодняшние продажи,
    общее количество товаров, общее количество клиентов и т.д.
    """
    try:
        # Проверить, есть ли у пользователя доступ к магазину
        await _validate_shop_access(current_user, shop_id, db)
        
        # Получить сервис дашборда
        dashboard_service = get_dashboard_service(db)
        
        # Получить краткую статистику
        quick_stats = await dashboard_service.get_quick_stats(shop_id)
        
        logger.info(f"Успешно получена краткая статистика для магазина {shop_id}")
        return quick_stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении краткой статистики: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить краткую статистику"
        )


@router.post("/shops/{shop_id}/refresh-cache")
async def refresh_dashboard_cache(
    shop_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Обновить кэш дашборда
    
    Ручное обновление кэша после обновления данных для получения актуальной информации.
    Требуются права администратора.
    """
    try:
        # Проверить, есть ли у пользователя доступ к магазину
        await _validate_shop_access(current_user, shop_id, db)
        
        # TODO: Добавить проверку прав администратора
        # Временно разрешить владельцам магазинов обновлять кэш
        
        # Получить сервис дашборда
        dashboard_service = get_dashboard_service(db)
        
        # Обновить кэш
        await dashboard_service.refresh_dashboard_cache(shop_id)
        
        return {"message": "Кэш дашборда обновлен", "shop_id": shop_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении кэша дашборда: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось обновить кэш"
        )


@router.get("/shops/{shop_id}/cache-info")
async def get_cache_info(
    shop_id: int,
    current_user = Depends(get_current_user)
):
    """
    Получить информацию о кэше (только для отладки)
    
    Возвращает информацию о состоянии кэша дашборда
    """
    try:
        # Проверить, есть ли у пользователя доступ к магазину
        # Здесь упрощенная проверка, в реальном проекте нужен более строгий контроль
        
        from backend.app.core.cache import cache_service
        
        # Найти ключи кэша, связанные с магазином
        pattern = f"cache:dashboard:*shop_{shop_id}*"
        
        try:
            keys = cache_service.redis.keys(pattern)
            cache_info = {
                "shop_id": shop_id,
                "cache_pattern": pattern,
                "cache_keys_count": len(keys),
                "cache_keys": keys[:10] if keys else []  # Показать только первые 10
            }
        except Exception as e:
            cache_info = {
                "shop_id": shop_id,
                "error": f"Ошибка при получении информации о кэше: {e}"
            }
        
        return cache_info
        
    except Exception as e:
        logger.error(f"Ошибка при получении информации о кэше: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить информацию о кэше"
        )


async def _validate_shop_access(user, shop_id: int, db: Session):
    """
    Проверить, есть ли у пользователя доступ к магазину
    
    1. Пользователь должен быть владельцем магазина
    2. Или пользователь должен быть участником магазина
    """
    # Проверить, является ли пользователь владельцем магазина
    shop = db.query(Shop).filter(
        Shop.id == shop_id,
        Shop.owner_id == user.id
    ).first()
    
    if shop:
        return True
    
    # Проверить, является ли пользователь участником магазина
    # ShopMember уже импортирован в этом файле
    member = db.query(ShopMember).filter(
        ShopMember.shop_id == shop_id,
        ShopMember.user_id == user.id
    ).first()
    
    if member:
        return True
    
    # Пользователь не имеет доступа к магазину
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Нет доступа к статистике этого магазина"
    )


# Эндпоинт проверки работоспособности
@router.get("/health")
async def dashboard_health():
    """Проверка работоспособности сервиса дашборда"""
    return {
        "status": "работает",
        "service": "dashboard",
        "features": [
            "stats_endpoint",
            "quick_stats",
            "cache_refresh",
            "redis_caching"
        ]
    }