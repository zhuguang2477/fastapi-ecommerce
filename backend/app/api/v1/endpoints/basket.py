# backend/app/api/v1/endpoints/baskets.py
"""
API конечные точки корзины покупок
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.core.security import get_current_user
from backend.app.services.basket_service import BasketService
from backend.app.schemas.basket import (
    BasketCreate, BasketUpdate, BasketResponse, BasketList,
    BasketItemCreate, BasketItemUpdate, BasketItemResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/shops/{shop_id}/baskets", response_model=BasketList)
async def get_baskets(
    shop_id: int = Path(..., description="ID магазина"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    status: Optional[str] = Query(None, description="Статус корзины"),
    is_guest: Optional[bool] = Query(None, description="Гостевая корзина"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить список корзин"""
    try:
        basket_service = BasketService(db)
        
        # Упрощенная реализация, в реальности должен быть более сложный запрос
        baskets = basket_service.db.query(basket_service.model).filter(
            basket_service.model.shop_id == shop_id
        )
        
        if status:
            baskets = baskets.filter(basket_service.model.status == status)
        if is_guest is not None:
            baskets = baskets.filter(basket_service.model.is_guest == is_guest)
        
        total = baskets.count()
        baskets = baskets.offset(skip).limit(limit).all()
        
        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        current_page = (skip // limit) + 1 if limit > 0 else 1
        
        return BasketList(
            baskets=baskets,
            total=total,
            page=current_page,
            page_size=limit,
            total_pages=total_pages
        )
    except Exception as e:
        logger.error(f"Ошибка при получении списка корзин: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить список корзин")


@router.get("/shops/{shop_id}/baskets/{basket_id}", response_model=BasketResponse)
async def get_basket(
    shop_id: int = Path(..., description="ID магазина"),
    basket_id: int = Path(..., description="ID корзины"),
    include_items: bool = Query(True, description="Включать товары"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить отдельную корзину"""
    try:
        basket_service = BasketService(db)
        basket = basket_service.get_basket(shop_id, basket_id)
        
        if not basket:
            raise HTTPException(status_code=404, detail="Корзина не найдена")
        
        return basket
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении корзины: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить корзину")


@router.get("/shops/{shop_id}/baskets/token/{basket_token}")
async def get_basket_by_token(
    shop_id: int = Path(..., description="ID магазина"),
    basket_token: str = Path(..., description="Токен корзины"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить корзину по токену"""
    try:
        basket_service = BasketService(db)
        basket = basket_service.get_basket_by_token(shop_id, basket_token)
        
        if not basket:
            raise HTTPException(status_code=404, detail="Корзина не найдена")
        
        return basket
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении корзины по токену: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить корзину по токену")


@router.get("/shops/{shop_id}/customers/{customer_id}/basket")
async def get_customer_basket(
    shop_id: int = Path(..., description="ID магазина"),
    customer_id: int = Path(..., description="ID клиента"),
    create_if_not_exists: bool = Query(True, description="Создать если не существует"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить корзину клиента"""
    try:
        basket_service = BasketService(db)
        basket = basket_service.get_customer_basket(shop_id, customer_id, create_if_not_exists)
        
        if not basket:
            raise HTTPException(status_code=404, detail="Корзина не найдена")
        
        return basket
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении корзины клиента: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить корзину клиента")


@router.post("/shops/{shop_id}/customers/{customer_id}/basket/items")
async def add_item_to_basket(
    shop_id: int = Path(..., description="ID магазина"),
    customer_id: int = Path(..., description="ID клиента"),
    item_data: BasketItemCreate = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Добавить товар в корзину"""
    try:
        basket_service = BasketService(db)
        
        # Получить корзину клиента
        basket = basket_service.get_customer_basket(shop_id, customer_id)
        if not basket:
            raise HTTPException(status_code=404, detail="Корзина не найдена")
        
        # Добавить товар
        basket_item = basket_service.add_item_to_basket(shop_id, basket.id, item_data)
        if not basket_item:
            raise HTTPException(status_code=400, detail="Не удалось добавить товар")
        
        return {
            "message": "Товар успешно добавлен",
            "basket_item": basket_item,
            "basket": basket
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при добавлении товара в корзину: {e}")
        raise HTTPException(status_code=500, detail="Не удалось добавить товар в корзину")


@router.put("/shops/{shop_id}/baskets/{basket_id}/items/{item_id}")
async def update_basket_item(
    shop_id: int = Path(..., description="ID магазина"),
    basket_id: int = Path(..., description="ID корзины"),
    item_id: int = Path(..., description="ID товара"),
    item_data: BasketItemUpdate = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Обновить товар в корзине"""
    try:
        basket_service = BasketService(db)
        basket_item = basket_service.update_basket_item(shop_id, basket_id, item_id, item_data)
        
        if not basket_item:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        return {
            "message": "Товар успешно обновлен",
            "basket_item": basket_item
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении товара в корзине: {e}")
        raise HTTPException(status_code=500, detail="Не удалось обновить товар в корзине")


@router.delete("/shops/{shop_id}/baskets/{basket_id}/items/{item_id}")
async def remove_item_from_basket(
    shop_id: int = Path(..., description="ID магазина"),
    basket_id: int = Path(..., description="ID корзины"),
    item_id: int = Path(..., description="ID товара"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Удалить товар из корзины"""
    try:
        basket_service = BasketService(db)
        success = basket_service.remove_item_from_basket(shop_id, basket_id, item_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        return {"message": "Товар успешно удален"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при удалении товара из корзины: {e}")
        raise HTTPException(status_code=500, detail="Не удалось удалить товар из корзины")


@router.delete("/shops/{shop_id}/baskets/{basket_id}/clear")
async def clear_basket(
    shop_id: int = Path(..., description="ID магазина"),
    basket_id: int = Path(..., description="ID корзины"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Очистить корзину"""
    try:
        basket_service = BasketService(db)
        success = basket_service.clear_basket(shop_id, basket_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Корзина не найдена")
        
        return {"message": "Корзина очищена"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при очистке корзины: {e}")
        raise HTTPException(status_code=500, detail="Не удалось очистить корзину")