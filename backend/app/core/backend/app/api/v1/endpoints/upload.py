# backend/app/api/v1/endpoints/upload.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Path
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging
import os

from backend.app.core.security import get_current_user, get_current_active_user
from backend.app.models.user import User
from backend.app.models.shop import ShopMember
from backend.app.schemas.upload import (
    UploadResponse, MultipleUploadResponse, 
    ImageUploadRequest, FileUploadConfig
)
from backend.app.services.upload_service import UploadService
from backend.app.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()
logger = logging.getLogger(__name__)

# Инициализация сервиса загрузки
try:
    upload_service = UploadService()
    logger.info("✅ Сервис загрузки инициализирован успешно")
except Exception as e:
    logger.error(f"❌ Ошибка инициализации сервиса загрузки: {e}")
    upload_service = None

# Функция зависимости: проверка прав администратора магазина
async def verify_shop_admin(
    shop_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Проверяет, является ли пользователь администратором магазина"""
    shop_member = db.query(ShopMember).filter(
        ShopMember.shop_id == shop_id,
        ShopMember.user_id == current_user.id,
        ShopMember.is_admin == True
    ).first()
    
    if not shop_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не являетесь администратором этого магазина"
        )
    
    return shop_id

# Загрузка одного изображения
@router.post("/shops/{shop_id}/upload/image", response_model=UploadResponse)
async def upload_image(
    shop_id: int = Depends(verify_shop_admin),
    file: UploadFile = File(...),
    folder: str = Form("products", description="Папка для сохранения"),
    resize_width: Optional[int] = Form(None, description="Ширина после изменения размера"),
    resize_height: Optional[int] = Form(None, description="Высота после изменения размера"),
    quality: int = Form(85, ge=1, le=100, description="Качество изображения")
):
    """
    Загрузить одно изображение
    
    - **file**: Файл изображения
    - **folder**: Папка для сохранения (products, shops, или другая пользовательская папка)
    - **resize_width**: Опционально, ширина для изменения размера
    - **resize_height**: Опционально, высота для изменения размера
    - **quality**: Качество изображения (1-100)
    """
    if upload_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис загрузки недоступен"
        )
    
    config = ImageUploadRequest(
        folder=folder,
        resize_width=resize_width,
        resize_height=resize_height,
        quality=quality
    )
    
    try:
        result = await upload_service.upload_image(file, folder, config)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка загрузки: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка загрузки: {str(e)}"
        )

# Загрузка нескольких изображений
@router.post("/shops/{shop_id}/upload/images", response_model=MultipleUploadResponse)
async def upload_multiple_images(
    shop_id: int = Depends(verify_shop_admin),
    files: List[UploadFile] = File(...),
    folder: str = Form("products", description="Папка для сохранения"),
    resize_width: Optional[int] = Form(None, description="Ширина после изменения размера"),
    resize_height: Optional[int] = Form(None, description="Высота после изменения размера"),
    quality: int = Form(85, description="Качество изображения")
):
    """
    Загрузить несколько изображений
    
    - **files**: Несколько файлов изображений
    - **folder**: Папка для сохранения
    - **resize_width**: Опционально, ширина для изменения размера
    - **resize_height**: Опционально, высота для изменения размера
    - **quality**: Качество изображения
    """
    if upload_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис загрузки недоступен"
        )
    
    config = ImageUploadRequest(
        folder=folder,
        resize_width=resize_width,
        resize_height=resize_height,
        quality=quality
    )
    
    try:
        result = await upload_service.upload_multiple_images(files, folder, config)
        
        return MultipleUploadResponse(
            files=result["files"],
            total_size=result["total_size"],
            success_count=result["success_count"],
            failed_count=result["failed_count"],
            failed_files=result["failed_files"]
        )
    except Exception as e:
        logger.error(f"Ошибка массовой загрузки: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка массовой загрузки: {str(e)}"
        )

# Загрузка изображений товара (специализированный эндпоинт для товаров)
@router.post("/shops/{shop_id}/products/{product_id}/upload-images")
async def upload_product_images(
    shop_id: int = Depends(verify_shop_admin),
    product_id: int = Path(..., description="ID товара"),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Загрузить изображения товара и привязать их к товару
    
    - **product_id**: ID товара
    - **files**: Файлы изображений товара
    """
    if upload_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис загрузки недоступен"
        )
    
    try:
        # Проверка существования товара и его принадлежности магазину
        from backend.app.services.product_service import ProductService
        product_service = ProductService(db)
        
        product = product_service.get_product(shop_id, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Товар не найден"
            )
        
        # Загрузка изображений
        upload_result = await upload_service.upload_multiple_images(files, "products")
        
        # Формирование данных об изображениях
        images_data = []
        for idx, file_result in enumerate(upload_result["files"]):
            images_data.append({
                "url": file_result.url,
                "thumbnail_url": file_result.thumbnail_url,
                "alt_text": product.name,
                "is_primary": idx == 0  # Первое изображение становится основным
            })
        
        # Обновление изображений товара
        success = product_service.update_product_images(shop_id, product_id, images_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка обновления изображений товара"
            )
        
        return {
            "message": "Изображения товара успешно загружены",
            "product_id": product_id,
            "uploaded_images": len(images_data),
            "images": images_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка загрузки изображений товара: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка загрузки изображений товара: {str(e)}"
        )

# Загрузка логотипа магазина
@router.post("/shops/{shop_id}/upload/logo")
async def upload_shop_logo(
    shop_id: int = Depends(verify_shop_admin),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Загрузить логотип магазина
    
    - **file**: Файл изображения логотипа
    """
    if upload_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис загрузки недоступен"
        )
    
    try:
        # Загрузка изображения
        result = await upload_service.upload_image(file, "shops")
        
        # Здесь можно обновить поле logo_url магазина
        # Пока просто возвращаем результат загрузки
        
        return {
            "message": "Логотип магазина успешно загружен",
            "logo_url": result.url,
            "thumbnail_url": result.thumbnail_url,
            "shop_id": shop_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка загрузки логотипа магазина: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка загрузки логотипа магазина: {str(e)}"
        )

# Удаление файла
@router.delete("/shops/{shop_id}/upload/delete")
async def delete_uploaded_file(
    shop_id: int = Depends(verify_shop_admin),
    file_url: str = Form(...)
):
    """
    Удалить загруженный файл
    
    - **file_url**: URL файла для удаления
    """
    if upload_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис загрузки недоступен"
        )
    
    try:
        success = upload_service.delete_file(file_url)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Файл не найден или не может быть удален"
            )
        
        return {"message": "Файл успешно удален", "file_url": file_url}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Ошибка удаления файла: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка удаления файла: {str(e)}"
        )

# Получение конфигурации загрузки
@router.get("/shops/{shop_id}/upload/config", response_model=FileUploadConfig)
async def get_upload_config(
    shop_id: int = Depends(verify_shop_admin)
):
    """Получить конфигурацию загрузки файлов"""
    return FileUploadConfig()

# Проверка статуса сервиса загрузки
@router.get("/shops/{shop_id}/upload/status")
async def check_upload_status(
    shop_id: int = Depends(verify_shop_admin)
):
    """Проверить статус сервиса загрузки"""
    if upload_service is None:
        return {
            "status": "error",
            "message": "Сервис загрузки не инициализирован",
            "available": False
        }
    
    # Проверка существования директории загрузок
    upload_dir = "uploads"
    exists = os.path.exists(upload_dir) and os.path.isdir(upload_dir)
    
    # Проверка поддиректорий
    subdirs = ["products", "shops", "temp"]
    subdirs_status = {}
    
    for subdir in subdirs:
        path = os.path.join(upload_dir, subdir)
        subdirs_status[subdir] = os.path.exists(path)
    
    return {
        "status": "healthy" if exists else "warning",
        "message": "Сервис загрузки работает нормально" if exists else "Директория загрузок не существует",
        "available": True,
        "upload_dir": upload_dir,
        "upload_dir_exists": exists,
        "subdirectories": subdirs_status,
        "max_file_size": "10MB",
        "allowed_formats": ["jpg", "jpeg", "png", "gif", "webp"]
    }