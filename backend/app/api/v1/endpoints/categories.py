# backend/app/api/v1/endpoints/categories.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from backend.app.database import get_db
from backend.app.core.security import get_current_user
from backend.app.schemas.category import (
    CategoryCreate, CategoryUpdate, CategoryInDB, 
    CategoryTree, CategoryList
)
from backend.app.services.category_service import CategoryService

router = APIRouter()
logger = logging.getLogger(__name__)

# Конечные точки управления категориями
@router.get("/shops/{shop_id}/categories/tree", response_model=List[CategoryTree])
async def get_category_tree(
    shop_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить древовидную структуру категорий"""
    try:
        category_service = CategoryService(db)
        categories = category_service.get_category_tree(shop_id)
        return categories
    except Exception as e:
        logger.error(f"Ошибка при получении дерева категорий: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить дерево категорий")

@router.get("/shops/{shop_id}/categories", response_model=CategoryList)
async def get_categories(
    shop_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    parent_id: Optional[int] = Query(None, description="ID родительской категории, 0 означает корневую категорию"),
    include_children: bool = Query(False, description="Включать ли дочерние категории"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить список категорий"""
    try:
        category_service = CategoryService(db)
        categories, total = category_service.get_categories(
            shop_id=shop_id,
            skip=skip,
            limit=limit,
            parent_id=parent_id,
            include_children=include_children
        )
        
        # Рассчитать общее количество страниц
        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        current_page = (skip // limit) + 1 if limit > 0 else 1
        
        return CategoryList(
            categories=categories,
            total=total,
            page=current_page,
            page_size=limit,
            total_pages=total_pages
        )
    except Exception as e:
        logger.error(f"Ошибка при получении списка категорий: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить список категорий")

@router.get("/shops/{shop_id}/categories/{category_id}", response_model=CategoryInDB)
async def get_category(
    shop_id: int,
    category_id: int = Path(..., description="ID категории"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить детальную информацию об одной категории"""
    try:
        category_service = CategoryService(db)
        category = category_service.get_category(shop_id, category_id)
        
        if not category:
            raise HTTPException(status_code=404, detail="Категория не найдена")
        
        return category
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении информации о категории: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить информацию о категории")

@router.post("/shops/{shop_id}/categories", response_model=CategoryInDB, status_code=status.HTTP_201_CREATED)
async def create_category(
    shop_id: int,
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Создать категорию"""
    try:
        category_service = CategoryService(db)
        category = category_service.create_category(shop_id, category_data)
        return category
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка при создании категории: {e}")
        raise HTTPException(status_code=500, detail="Не удалось создать категорию")

@router.put("/shops/{shop_id}/categories/{category_id}", response_model=CategoryInDB)
async def update_category(
    shop_id: int,
    category_id: int = Path(..., description="ID категории"),
    update_data: CategoryUpdate = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Обновить категорию"""
    try:
        category_service = CategoryService(db)
        category = category_service.update_category(shop_id, category_id, update_data)
        
        if not category:
            raise HTTPException(status_code=404, detail="Категория не найдена")
        
        return category
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении категории: {e}")
        raise HTTPException(status_code=500, detail="Не удалось обновить категорию")

@router.delete("/shops/{shop_id}/categories/{category_id}")
async def delete_category(
    shop_id: int,
    category_id: int = Path(..., description="ID категории"),
    force: bool = Query(False, description="Принудительное удаление (категории, содержащие товары)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Удалить категорию"""
    try:
        category_service = CategoryService(db)
        success = category_service.delete_category(shop_id, category_id, force)
        
        if not success:
            raise HTTPException(status_code=404, detail="Категория не найдена")
        
        return {"message": "Категория успешно удалена"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при удалении категории: {e}")
        raise HTTPException(status_code=500, detail="Не удалось удалить категорию")

@router.patch("/shops/{shop_id}/categories/{category_id}/move")
async def move_category(
    shop_id: int,
    category_id: int = Path(..., description="ID категории"),
    new_parent_id: Optional[int] = Query(None, description="ID новой родительской категории"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Переместить категорию под новую родительскую категорию"""
    try:
        category_service = CategoryService(db)
        success = category_service.move_category(shop_id, category_id, new_parent_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Категория не найдена")
        
        return {"message": "Категория успешно перемещена"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при перемещении категории: {e}")
        raise HTTPException(status_code=500, detail="Не удалось переместить категорию")

@router.get("/shops/{shop_id}/categories/stats")
async def get_category_stats(
    shop_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить статистику по категориям"""
    try:
        category_service = CategoryService(db)
        stats = category_service.get_category_stats(shop_id)
        return stats
    except Exception as e:
        logger.error(f"Ошибка при получении статистики категорий: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить статистику категорий")