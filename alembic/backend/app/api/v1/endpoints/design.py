# backend/app/api/v1/endpoints/design.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from backend.app.database import get_db
from backend.app.core.security import get_current_user
from backend.app.schemas.design import ShopDesignResponse, ShopDesignUpdate, UploadLogoRequest
from backend.app.services.design_service import DesignService
from backend.app.services.upload_service import UploadService

router = APIRouter()
logger = logging.getLogger(__name__)

# Конечные точки управления дизайном магазина
@router.get("/shops/{shop_id}/design", response_model=ShopDesignResponse)
async def get_shop_design(
    shop_id: int = Path(..., description="ID магазина"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить дизайн магазина"""
    try:
        design_service = DesignService(db)
        design = design_service.get_design(shop_id)
        
        if not design:
            # Если дизайн не существует, вернуть значения по умолчанию
            design = design_service.create_or_update_design(
                shop_id, 
                ShopDesignUpdate()
            )
        
        return design
    except Exception as e:
        logger.error(f"Ошибка при получении дизайна магазина: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить дизайн магазина")

@router.put("/shops/{shop_id}/design", response_model=ShopDesignResponse)
async def update_shop_design(
    shop_id: int = Path(..., description="ID магазина"),
    design_data: ShopDesignUpdate = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Обновить дизайн магазина"""
    try:
        design_service = DesignService(db)
        design = design_service.create_or_update_design(shop_id, design_data)
        return design
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка при обновлении дизайна магазина: {e}")
        raise HTTPException(status_code=500, detail="Не удалось обновить дизайн магазина")

@router.patch("/shops/{shop_id}/design")
async def patch_shop_design(
    shop_id: int = Path(..., description="ID магазина"),
    update_data: dict = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Частичное обновление дизайна магазина"""
    try:
        design_service = DesignService(db)
        design = design_service.create_or_update_design(shop_id, ShopDesignUpdate(**update_data))
        
        if not design:
            raise HTTPException(status_code=404, detail="Дизайн магазина не найден")
        
        return design
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при частичном обновлении дизайна магазина: {e}")
        raise HTTPException(status_code=500, detail="Не удалось частично обновить дизайн магазина")

@router.post("/shops/{shop_id}/design/upload-logo")
async def upload_logo(
    shop_id: int = Path(..., description="ID магазина"),
    file: UploadFile = File(...),
    image_type: str = Query("logo", description="Тип изображения: logo, favicon, banner"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Загрузить логотип или связанное изображение"""
    try:
        # Проверить тип файла
        allowed_types = ["logo", "favicon", "banner"]
        if image_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Тип изображения должен быть одним из: {', '.join(allowed_types)}"
            )
        
        # Загрузить изображение
        upload_service = UploadService()
        result = await upload_service.upload_image(file, folder="shops")
        
        # Обновить дизайн магазина
        design_service = DesignService(db)
        design = design_service.get_design(shop_id)
        
        if not design:
            # Если дизайн не существует, создать дизайн по умолчанию
            design = design_service.create_or_update_design(
                shop_id, 
                ShopDesignUpdate()
            )
        
        # Обновить соответствующее поле в зависимости от типа изображения
        update_data = {}
        if image_type == "logo":
            update_data["logo_url"] = result.url
        elif image_type == "favicon":
            update_data["favicon_url"] = result.url
        elif image_type == "banner":
            update_data["banner_url"] = result.url
        
        design = design_service.create_or_update_design(
            shop_id, 
            ShopDesignUpdate(**update_data)
        )
        
        return {
            "message": f"{image_type} успешно загружен",
            "url": result.url,
            "design": design
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при загрузке логотипа: {e}")
        raise HTTPException(status_code=500, detail=f"Не удалось загрузить {image_type}")

@router.post("/shops/{shop_id}/design/hero-banners")
async def add_hero_banner(
    shop_id: int = Path(..., description="ID магазина"),
    image_url: str = Query(..., description="URL изображения"),
    title: Optional[str] = Query(None, description="Заголовок баннера"),
    subtitle: Optional[str] = Query(None, description="Подзаголовок баннера"),
    link_url: Optional[str] = Query(None, description="URL ссылки"),
    button_text: Optional[str] = Query("Узнать больше", description="Текст кнопки"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Добавить главный баннер"""
    try:
        banner_data = {
            "image_url": image_url,
            "title": title,
            "subtitle": subtitle,
            "link_url": link_url,
            "button_text": button_text
        }
        
        design_service = DesignService(db)
        success = design_service.add_hero_banner(shop_id, banner_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Не удалось добавить главный баннер")
        
        return {"message": "Главный баннер успешно добавлен"}
    except Exception as e:
        logger.error(f"Ошибка при добавлении главного баннера: {e}")
        raise HTTPException(status_code=500, detail="Не удалось добавить главный баннер")

@router.delete("/shops/{shop_id}/design/hero-banners/{banner_index}")
async def remove_hero_banner(
    shop_id: int = Path(..., description="ID магазина"),
    banner_index: int = Path(..., ge=0, description="Индекс баннера"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Удалить главный баннер"""
    try:
        design_service = DesignService(db)
        success = design_service.remove_hero_banner(shop_id, banner_index)
        
        if not success:
            raise HTTPException(status_code=404, detail="Баннер не найден")
        
        return {"message": "Главный баннер успешно удален"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при удалении главного баннера: {e}")
        raise HTTPException(status_code=500, detail="Не удалось удалить главный баннер")