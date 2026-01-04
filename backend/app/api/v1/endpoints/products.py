# backend/app/api/v1/endpoints/products.py
"""
商品管理API端点
"""
# backend/app/api/v1/endpoints/product.py
import logging
import csv
import json
from typing import Optional, List, Dict, Any
from io import StringIO
from datetime import datetime
from fastapi import (
    APIRouter, Depends, HTTPException, status, Path,
    Query, UploadFile, File, Form, BackgroundTasks
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.app.database import get_db
from backend.app.core.security import get_current_user, get_current_active_user
from backend.app.services.product_service import ProductService
from backend.app.services.upload_service import UploadService
from backend.app.schemas.product import (
    ProductCreate, ProductUpdate, ProductInDB, ProductList,
    ProductSearch, ProductStats, ProductStatus, ProductResponse,
    ProductImageUpload, ProductInventoryUpdate,
    ProductBatchUpdate, ProductExportRequest
)
from backend.app.services.category_service import CategoryService
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["products"])

def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    """Получить экземпляр сервиса товаров"""
    return ProductService(db)


def get_upload_service() -> UploadService:
    """Получить экземпляр сервиса загрузки"""
    return UploadService()


@router.get("/", response_model=ProductList)
async def get_products(
    shop_id: int = Query(..., description="ID магазина"),
    skip: int = Query(0, ge=0, description="Количество пропущенных"),
    limit: int = Query(100, ge=1, le=1000, description="Количество на странице"),
    category_id: Optional[int] = Query(None, description="ID категории"),
    status: Optional[str] = Query(None, description="Статус товара"),
    is_featured: Optional[bool] = Query(None, description="Рекомендуемый товар"),
    min_price: Optional[float] = Query(None, ge=0, description="Минимальная цена"),
    max_price: Optional[float] = Query(None, ge=0, description="Максимальная цена"),
    in_stock: Optional[bool] = Query(None, description="Есть в наличии"),
    search_query: Optional[str] = Query(None, description="Поисковый запрос"),
    sort_by: str = Query("created_at", description="Поле сортировки"),
    sort_order: str = Query("desc", description="Направление сортировки"),
    current_user = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Получить список товаров (с пагинацией, фильтрацией и поиском)
    """
    try:
        # Проверить права пользователя
        await _validate_shop_access(current_user, shop_id, product_service.db)
        
        # Построить параметры поиска
        search_params = ProductSearch(
            query=search_query,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            status=status,
            is_featured=is_featured,
            in_stock=in_stock
        )
        
        # Получить список товаров
        products, total = product_service.get_products(
            shop_id=shop_id,
            skip=skip,
            limit=limit,
            search_params=search_params,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Вычислить информацию о пагинации
        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        current_page = (skip // limit) + 1 if limit > 0 else 1
        
        logger.info(f"Пользователь {current_user.id} получил список товаров магазина {shop_id}")
        
        return ProductList(
            products=products,
            total=total,
            page=current_page,
            page_size=limit,
            total_pages=total_pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении списка товаров: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить список товаров"
        )


@router.get("/shops/{shop_id}/products/{product_id}", response_model=ProductResponse)
async def get_product(
    shop_id: int = Path(..., description="ID магазина"),     
    product_id: int = Path(..., description="ID товара"), 
    current_user = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Получить детальную информацию о товаре
    """
    try:
        # Проверить права пользователя
        await _validate_shop_access(current_user, shop_id, product_service.db)
        
        # Получить товар
        product = product_service.get_product(shop_id, product_id)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Товар не найден"
            )
        
        logger.info(f"Пользователь {current_user.id} просмотрел товар {product_id}")
        
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении информации о товаре: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить информацию о товаре"
        )


@router.post("/", response_model=ProductInDB)
async def create_product(
    shop_id: int = Query(..., description="ID магазина"),
    product_data: ProductCreate = None,
    current_user = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Создать новый товар
    """
    try:
        # Проверить права пользователя (требуются права администратора)
        await _validate_shop_admin_access(current_user, shop_id, product_service.db)
        
        # Создать товар
        product = product_service.create_product(shop_id, product_data)
        
        logger.info(f"Пользователь {current_user.id} создал товар: {product.name}")
        
        return product
        
    except ValueError as e:
        logger.warning(f"Ошибка параметров при создании товара: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Ошибка при создании товара: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось создать товар"
        )


@router.put("/{product_id}", response_model=ProductInDB)
async def update_product(
    shop_id: int = Path(..., description="ID магазина"),
    product_id: int = Path(..., description="ID товара"),
    update_data: ProductUpdate = None,
    current_user = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Обновить информацию о товаре
    """
    try:
        # Проверить права пользователя (требуются права администратора)
        await _validate_shop_admin_access(current_user, shop_id, product_service.db)
        
        # Обновить товар
        product = product_service.update_product(shop_id, product_id, update_data)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Товар не найден"
            )
        
        logger.info(f"Пользователь {current_user.id} обновил товар {product_id}")
        
        return product
        
    except ValueError as e:
        logger.warning(f"Ошибка параметров при обновлении товара: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Ошибка при обновлении товара: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось обновить товар"
        )


@router.patch("/{product_id}/status")
async def update_product_status(
    shop_id: int = Path(..., description="ID магазина"),
    product_id: int = Path(..., description="ID товара"),
    status: str = Query(..., description="Новый статус"),
    reason: Optional[str] = Query(None, description="Причина изменения статуса"),
    current_user = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Обновить статус товара
    
    Допустимые статусы: 
    - draft: Черновик
    - active: Активен
    - inactive: Неактивен
    - archived: Архивный
    - discontinued: Снят с производства
    """
    try:
        # Проверить права пользователя (требуются права администратора)
        await _validate_shop_admin_access(current_user, shop_id, product_service.db)
        
        # Валидация статуса
        valid_statuses = ["draft", "active", "inactive", "archived", "discontinued"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неверный статус. Допустимые значения: {', '.join(valid_statuses)}"
            )
        
        # Обновить статус товара
        success = product_service.update_product_status(
            shop_id, product_id, status, reason
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Товар не найден"
            )
        
        logger.info(f"Пользователь {current_user.id} обновил статус товара {product_id} на {status}")
        
        return {"message": "Статус товара успешно обновлен", "status": status}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении статуса товара: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось обновить статус товара"
        )
    
@router.patch("/batch-status")
async def batch_update_product_status(
    shop_id: int = Path(..., description="ID магазина"),
    product_ids: List[int] = Query(..., description="ID товаров"),
    status: str = Query(..., description="Новый статус"),
    reason: Optional[str] = Query(None, description="Причина изменения статуса"),
    current_user = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Массовое обновление статуса товаров
    """
    try:
        # Проверить права пользователя (требуются права администратора)
        await _validate_shop_admin_access(current_user, shop_id, product_service.db)
        
        # Валидация статуса
        valid_statuses = ["draft", "active", "inactive", "archived", "discontinued"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неверный статус. Допустимые значения: {', '.join(valid_statuses)}"
            )
        
        updated_count = 0
        errors = []
        
        for product_id in product_ids:
            try:
                success = product_service.update_product_status(
                    shop_id, product_id, status, reason
                )
                if success:
                    updated_count += 1
                else:
                    errors.append(f"Товар {product_id} не найден")
            except Exception as e:
                errors.append(f"Ошибка обновления товара {product_id}: {str(e)}")
        
        return {
            "message": f"Статус обновлен для {updated_count} товаров",
            "updated_count": updated_count,
            "total_requested": len(product_ids),
            "errors": errors if errors else None
        }
        
    except Exception as e:
        logger.error(f"Ошибка при массовом обновлении статуса товаров: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось обновить статус товаров"
        )


@router.patch("/{product_id}/inventory")
async def update_product_inventory(
    shop_id: int = Path(..., description="ID магазина"),
    product_id: int = Path(..., description="ID товара"),
    inventory_update: ProductInventoryUpdate = None,
    current_user = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Обновить складские запасы товара
    """
    try:
        # Проверить права пользователя (требуются права администратора)
        await _validate_shop_admin_access(current_user, shop_id, product_service.db)
        
        # Скорректировать запасы
        success = product_service.adjust_stock(
            shop_id,
            product_id,
            inventory_update.quantity_change,
            inventory_update.operation
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Товар не найден или не удалось скорректировать запасы"
            )
        
        # Получить обновленную информацию о товаре
        product = product_service.get_product(shop_id, product_id)
        
        logger.info(f"Пользователь {current_user.id} скорректировал запасы товара {product_id}")
        
        return {
            "message": "Запасы успешно обновлены",
            "product_id": product_id,
            "new_stock_quantity": product.stock_quantity,
            "operation": inventory_update.operation
        }
        
    except ValueError as e:
        logger.warning(f"Ошибка параметров при обновлении запасов: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Ошибка при обновлении запасов: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось обновить запасы"
        )


@router.delete("/{product_id}")
async def delete_product(
    shop_id: int = Path(..., description="ID магазина"),
    product_id: int = Path(..., description="ID товара"),
    current_user = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Удалить товар (мягкое удаление, изменение статуса на снят с продажи)
    """
    try:
        # Проверить права пользователя (требуются права администратора)
        await _validate_shop_admin_access(current_user, shop_id, product_service.db)
        
        # Удалить товар
        success = product_service.delete_product(shop_id, product_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Товар не найден"
            )
        
        logger.info(f"Пользователь {current_user.id} удалил товар {product_id}")
        
        return {"message": "Товар снят с продажи"}
        
    except Exception as e:
        logger.error(f"Ошибка при удалении товара: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось удалить товар"
        )


@router.post("/upload-images")
async def upload_product_images(
    shop_id: int = Path(..., description="ID магазина"),
    files: List[UploadFile] = File(...),
    product_id: Optional[int] = Form(None, description="ID товара (для загрузки изображений существующего товара)"),
    folder: str = Form("products", description="Папка для хранения"),
    resize_width: Optional[int] = Form(None, description="Ширина для изменения размера"),
    resize_height: Optional[int] = Form(None, description="Высота для изменения размера"),
    quality: int = Form(85, description="Качество изображения"),
    current_user = Depends(get_current_user),
    upload_service: UploadService = Depends(get_upload_service),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Загрузить изображения товара
    
    Поддерживает загрузку одного или нескольких изображений
    Если указан product_id, изображения будут привязаны к этому товару
    """
    try:
        # Проверить права пользователя
        await _validate_shop_access(current_user, shop_id, product_service.db)
        
        # Если указан product_id, проверить существование товара и принадлежность магазину
        if product_id:
            product = product_service.get_product(shop_id, product_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Товар не найден"
                )
        
        # Настроить параметры загрузки
        from backend.app.schemas.upload import ImageUploadRequest
        config = ImageUploadRequest(
            folder=folder,
            resize_width=resize_width,
            resize_height=resize_height,
            quality=quality
        )
        
        # Загрузить изображения
        upload_result = await upload_service.upload_multiple_images(files, folder, config)
        
        # Если указан product_id, привязать изображения к товару
        if product_id and upload_result["success_count"] > 0:
            # Построить данные изображений
            images_data = []
            for uploaded_file in upload_result["files"]:
                images_data.append({
                    "url": uploaded_file.url,
                    "thumbnail_url": uploaded_file.thumbnail_url,
                    "alt_text": None,  # Можно добавить alt_text здесь
                    "is_primary": False
                })
            
            # Обновить изображения товара
            product_service.update_product_images(shop_id, product_id, images_data)
        
        logger.info(f"Пользователь {current_user.id} загрузил {upload_result['success_count']} изображений")
        
        return upload_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при загрузке изображений: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось загрузить изображения: {str(e)}"
        )


@router.post("/{product_id}/images")
async def update_product_images(
    shop_id: int = Path(..., description="ID магазина"),
    product_id: int = Path(..., description="ID товара"),
    image_data: ProductImageUpload = None,
    current_user = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Обновить изображения товара (замена существующих изображений)
    """
    try:
        # Проверить права пользователя (требуются права администратора)
        await _validate_shop_admin_access(current_user, shop_id, product_service.db)
        
        # Проверить существование товара
        product = product_service.get_product(shop_id, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Товар не найден"
            )
        
        # Обновить изображения товара
        success = product_service.update_product_images(
            shop_id, product_id, image_data.images
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось обновить изображения товара"
            )
        
        logger.info(f"Пользователь {current_user.id} обновил изображения товара {product_id}")
        
        return {"message": "Изображения товара успешно обновлены"}
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении изображений товара: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось обновить изображения товара"
        )


@router.post("/batch-update")
async def batch_update_products(
    shop_id: int = Path(..., description="ID магазина"),
    batch_update: ProductBatchUpdate = None,
    current_user = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Массовое обновление товаров
    """
    try:
        # Проверить права пользователя (требуются права администратора)
        await _validate_shop_admin_access(current_user, shop_id, product_service.db)
        
        # Выполнить массовое обновление
        updated_count = product_service.bulk_update_products(
            shop_id, batch_update.product_ids, batch_update.update_data
        )
        
        logger.info(f"Пользователь {current_user.id} массово обновил {updated_count} товаров")
        
        return {
            "message": "Массовое обновление успешно выполнено",
            "updated_count": updated_count
        }
        
    except ValueError as e:
        logger.warning(f"Ошибка параметров при массовом обновлении: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Ошибка при массовом обновлении товаров: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось выполнить массовое обновление товаров"
        )


@router.post("/{product_id}/duplicate")
async def duplicate_product(
    shop_id: int = Path(..., description="ID магазина"),
    product_id: int = Path(..., description="ID товара"),
    new_name: Optional[str] = Query(None, description="Новое название товара"),
    current_user = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Дублировать товар
    """
    try:
        # Проверить права пользователя (требуются права администратора)
        await _validate_shop_admin_access(current_user, shop_id, product_service.db)
        
        # Дублировать товар
        new_product = product_service.duplicate_product(shop_id, product_id, new_name)
        
        if not new_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Товар не найден"
            )
        
        logger.info(f"Пользователь {current_user.id} скопировал товар {product_id} -> {new_product.id}")
        
        return {
            "message": "Товар успешно скопирован",
            "original_product_id": product_id,
            "new_product_id": new_product.id,
            "new_product_name": new_product.name
        }
        
    except Exception as e:
        logger.error(f"Ошибка при копировании товара: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось скопировать товар"
        )


@router.get("/stats/summary")
async def get_product_stats(
    shop_id: int = Path(..., description="ID магазина"),
    current_user = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Получить сводную статистику по товарам
    """
    try:
        # Проверить права пользователя
        await _validate_shop_access(current_user, shop_id, product_service.db)
        
        # Получить статистику
        stats = product_service.get_product_stats(shop_id)
        
        # Получить товары с низким запасом
        low_stock = product_service.get_low_stock_products(shop_id)
        
        # Получить отсутствующие товары
        out_of_stock = product_service.get_out_of_stock_products(shop_id)
        
        return {
            "summary": stats,
            "low_stock_count": len(low_stock),
            "out_of_stock_count": len(out_of_stock),
            "low_stock_products": [
                {"id": p.id, "name": p.name, "stock_quantity": p.stock_quantity}
                for p in low_stock[:10]  # Вернуть только первые 10
            ],
            "out_of_stock_products": [
                {"id": p.id, "name": p.name}
                for p in out_of_stock[:10]  # Вернуть только первые 10
            ]
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики товаров: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить статистику товаров"
        )


@router.post("/export")
async def export_products(
    shop_id: int = Path(..., description="ID магазина"),
    export_request: ProductExportRequest = None,
    current_user = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Экспорт данных о товарах
    """
    try:
        # Проверить права пользователя
        await _validate_shop_access(current_user, shop_id, product_service.db)
        
        # Получить данные о товарах
        products, total = product_service.get_products(
            shop_id=shop_id,
            skip=0,
            limit=10000,  # Ограничение количества экспортируемых записей
            search_params=export_request.filter if export_request else None
        )
        
        # Подготовить данные для экспорта
        export_data = []
        for product in products:
            product_dict = {}
            
            for column in export_request.columns if export_request else ["id", "name", "price"]:
                if hasattr(product, column):
                    value = getattr(product, column)
                    
                    # Обработать специальные поля
                    if column in ["tags", "attributes"] and value:
                        value = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
                    elif isinstance(value, datetime):
                        value = value.strftime("%Y-%m-%d %H:%M:%S")
                    
                    product_dict[column] = value
            
            export_data.append(product_dict)
        
        # Сгенерировать имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"products_export_{shop_id}_{timestamp}"
        
        # Сгенерировать ответ в зависимости от формата
        if export_request.format == "csv":
            # Сгенерировать CSV
            output = StringIO()
            
            if export_data:
                writer = csv.DictWriter(output, fieldnames=export_request.columns)
                writer.writeheader()
                writer.writerows(export_data)
            
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}.csv"
                }
            )
        
        elif export_request.format == "json":
            # Сгенерировать JSON
            return {
                "filename": f"{filename}.json",
                "total_count": len(export_data),
                "data": export_data
            }
        
        else:
            # Для Excel требуются дополнительные библиотеки
            return {
                "filename": f"{filename}.xlsx",
                "total_count": len(export_data),
                "data": export_data,
                "format": "excel"
            }
        
    except Exception as e:
        logger.error(f"Ошибка при экспорте товаров: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось экспортировать товары: {str(e)}"
        )


@router.get("/search/full-text")
async def search_products_full_text(
    shop_id: int = Path(..., description="ID магазина"),
    query: str = Query(..., description="Поисковый запрос"),
    limit: int = Query(50, ge=1, le=200, description="Лимит возвращаемых записей"),
    current_user = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Полнотекстовый поиск товаров
    """
    try:
        # Проверить права пользователя
        await _validate_shop_access(current_user, shop_id, product_service.db)
        
        # Поиск товаров
        products = product_service.search_products_full_text(shop_id, query, limit)
        
        return {
            "query": query,
            "results_count": len(products),
            "products": products
        }
        
    except Exception as e:
        logger.error(f"Ошибка при поиске товаров: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось выполнить поиск товаров"
        )


# ===== Вспомогательные функции проверки прав доступа =====

async def _validate_shop_access(user, shop_id: int, db: Session):
    """Проверить, имеет ли пользователь доступ к магазину"""
    from backend.app.models.shop import Shop, ShopMember
    
    # Проверить, является ли пользователь владельцем магазина
    shop = db.query(Shop).filter(
        Shop.id == shop_id,
        Shop.owner_id == user.id
    ).first()
    
    if shop:
        return True
    
    # Проверить, является ли пользователь участником магазина
    member = db.query(ShopMember).filter(
        ShopMember.shop_id == shop_id,
        ShopMember.user_id == user.id
    ).first()
    
    if member:
        return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Нет доступа к товарам этого магазина"
    )


async def _validate_shop_admin_access(user, shop_id: int, db: Session):
    """Проверить, является ли пользователь администратором или владельцем магазина"""
    from backend.app.models.shop import Shop, ShopMember
    
    # Проверить, является ли пользователь владельцем магазина
    shop = db.query(Shop).filter(
        Shop.id == shop_id,
        Shop.owner_id == user.id
    ).first()
    
    if shop:
        return True
    
    # Проверить, является ли пользователь администратором магазина
    member = db.query(ShopMember).filter(
        ShopMember.shop_id == shop_id,
        ShopMember.user_id == user.id,
        ShopMember.is_admin == True
    ).first()
    
    if member:
        return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Требуются права администратора для операций с товарами"
    )


# Конечная точка проверки работоспособности
@router.get("/health")
async def products_health():
    """Проверка работоспособности сервиса товаров"""
    return {
        "status": "работает",
        "service": "товары",
        "endpoints": [
            "GET /products",
            "GET /products/{product_id}",
            "POST /products",
            "PUT /products/{product_id}",
            "PATCH /products/{product_id}/status",
            "PATCH /products/{product_id}/inventory",
            "DELETE /products/{product_id}",
            "POST /products/upload-images",
            "POST /products/{product_id}/images",
            "POST /products/batch-update",
            "POST /products/{product_id}/duplicate",
            "GET /products/stats/summary",
            "POST /products/export",
            "GET /products/search/full-text"
        ]
    }