# backend/app/api/v1/endpoints/setting.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import Optional
import logging

from backend.app.database import get_db
from backend.app.core.security import get_current_user
from backend.app.schemas.shop_settings import ShopSettingsResponse, ShopSettingsUpdate
from backend.app.services.shop_settings_service import SettingsService

router = APIRouter()
logger = logging.getLogger(__name__)

# Конечные точки управления настройками магазина
@router.get("/shops/{shop_id}/settings", response_model=ShopSettingsResponse)
async def get_shop_settings(
    shop_id: int = Path(..., description="ID магазина"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить настройки магазина"""
    try:
        settings_service = SettingsService(db)
        settings = settings_service.get_settings(shop_id)
        
        if not settings:
            # Если настройки не существуют, вернуть значения по умолчанию
            settings = settings_service.create_or_update_settings(
                shop_id, 
                ShopSettingsUpdate()
            )
        
        return settings
    except Exception as e:
        logger.error(f"Ошибка получения настроек магазина: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить настройки магазина")

@router.put("/shops/{shop_id}/settings", response_model=ShopSettingsResponse)
async def update_shop_settings(
    shop_id: int = Path(..., description="ID магазина"),
    settings_data: ShopSettingsUpdate = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Обновить настройки магазина"""
    try:
        settings_service = SettingsService(db)
        settings = settings_service.create_or_update_settings(shop_id, settings_data)
        return settings
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка обновления настроек магазина: {e}")
        raise HTTPException(status_code=500, detail="Не удалось обновить настройки магазина")

@router.patch("/shops/{shop_id}/settings")
async def patch_shop_settings(
    shop_id: int = Path(..., description="ID магазина"),
    update_data: dict = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Частичное обновление настроек магазина"""
    try:
        settings_service = SettingsService(db)
        settings = settings_service.update_settings_partial(shop_id, update_data)
        
        if not settings:
            raise HTTPException(status_code=404, detail="Настройки магазина не найдены")
        
        return settings
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка частичного обновления настроек магазина: {e}")
        raise HTTPException(status_code=500, detail="Не удалось частично обновить настройки магазина")

@router.post("/shops/{shop_id}/settings/reset")
async def reset_shop_settings(
    shop_id: int = Path(..., description="ID магазина"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Сбросить настройки магазина к значениям по умолчанию"""
    try:
        settings_service = SettingsService(db)
        success = settings_service.reset_settings(shop_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Не удалось сбросить настройки магазина")
        
        return {"message": "Настройки магазина сброшены к значениям по умолчанию"}
    except Exception as e:
        logger.error(f"Ошибка сброса настроек магазина: {e}")
        raise HTTPException(status_code=500, detail="Не удалось сбросить настройки магазина")