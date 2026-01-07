# backend/app/api/v1/endpoints/recipients.py
"""
API-эндпоинты для управления получателями
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.core.security import get_current_user
from backend.app.services.recipient_service import RecipientService
from backend.app.schemas.recipient import (
    RecipientCreate, RecipientUpdate, RecipientResponse, RecipientList
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/shops/{shop_id}/customers/{customer_id}/recipients", response_model=RecipientList)
async def get_customer_recipients(
    shop_id: int = Path(..., description="ID магазина"),
    customer_id: int = Path(..., description="ID клиента"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    address_type: Optional[str] = Query(None, description="Тип адреса: shipping, billing, both"),
    is_active: Optional[bool] = Query(None, description="Активен ли получатель"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить список получателей клиента"""
    try:
        recipient_service = RecipientService(db)
        recipients, total = recipient_service.get_customer_recipients(
            shop_id=shop_id,
            customer_id=customer_id,
            skip=skip,
            limit=limit,
            address_type=address_type,
            is_active=is_active
        )
        
        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        current_page = (skip // limit) + 1 if limit > 0 else 1
        
        return RecipientList(
            recipients=recipients,
            total=total,
            page=current_page,
            page_size=limit,
            total_pages=total_pages
        )
    except Exception as e:
        logger.error(f"Ошибка при получении списка получателей: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить список получателей")


@router.get("/shops/{shop_id}/recipients/{recipient_id}", response_model=RecipientResponse)
async def get_recipient(
    shop_id: int = Path(..., description="ID магазина"),
    recipient_id: int = Path(..., description="ID получателя"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить информацию о конкретном получателе"""
    try:
        recipient_service = RecipientService(db)
        recipient = recipient_service.get_recipient(shop_id, recipient_id)
        
        if not recipient:
            raise HTTPException(status_code=404, detail="Получатель не найден")
        
        return recipient
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении информации о получателе: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить информацию о получателе")


@router.post("/shops/{shop_id}/customers/{customer_id}/recipients", response_model=RecipientResponse, status_code=status.HTTP_201_CREATED)
async def create_recipient(
    shop_id: int = Path(..., description="ID магазина"),
    customer_id: int = Path(..., description="ID клиента"),
    recipient_data: RecipientCreate = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Создать нового получателя"""
    try:
        recipient_service = RecipientService(db)
        recipient = recipient_service.create_recipient(shop_id, customer_id, recipient_data)
        
        if not recipient:
            raise HTTPException(status_code=400, detail="Не удалось создать получателя")
        
        return recipient
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при создании получателя: {e}")
        raise HTTPException(status_code=500, detail="Не удалось создать получателя")


@router.put("/shops/{shop_id}/recipients/{recipient_id}", response_model=RecipientResponse)
async def update_recipient(
    shop_id: int = Path(..., description="ID магазина"),
    recipient_id: int = Path(..., description="ID получателя"),
    recipient_data: RecipientUpdate = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Обновить информацию о получателе"""
    try:
        recipient_service = RecipientService(db)
        recipient = recipient_service.update_recipient(shop_id, recipient_id, recipient_data)
        
        if not recipient:
            raise HTTPException(status_code=404, detail="Получатель не найден")
        
        return recipient
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении информации о получателе: {e}")
        raise HTTPException(status_code=500, detail="Не удалось обновить информацию о получателе")


@router.delete("/shops/{shop_id}/recipients/{recipient_id}")
async def delete_recipient(
    shop_id: int = Path(..., description="ID магазина"),
    recipient_id: int = Path(..., description="ID получателя"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Удалить получателя"""
    try:
        recipient_service = RecipientService(db)
        success = recipient_service.delete_recipient(shop_id, recipient_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Получатель не найден или имеет связанные заказы")
        
        return {"message": "Получатель успешно удален"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при удалении получателя: {e}")
        raise HTTPException(status_code=500, detail="Не удалось удалить получателя")


@router.get("/shops/{shop_id}/customers/{customer_id}/default-shipping")
async def get_default_shipping_address(
    shop_id: int = Path(..., description="ID магазина"),
    customer_id: int = Path(..., description="ID клиента"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить адрес доставки по умолчанию"""
    try:
        recipient_service = RecipientService(db)
        recipient = recipient_service.get_default_shipping_address(shop_id, customer_id)
        
        if not recipient:
            raise HTTPException(status_code=404, detail="Адрес доставки по умолчанию не установлен")
        
        return recipient
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении адреса доставки по умолчанию: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить адрес доставки по умолчанию")


@router.get("/shops/{shop_id}/customers/{customer_id}/default-billing")
async def get_default_billing_address(
    shop_id: int = Path(..., description="ID магазина"),
    customer_id: int = Path(..., description="ID клиента"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить адрес для выставления счетов по умолчанию"""
    try:
        recipient_service = RecipientService(db)
        recipient = recipient_service.get_default_billing_address(shop_id, customer_id)
        
        if not recipient:
            raise HTTPException(status_code=404, detail="Адрес для выставления счетов по умолчанию не установлен")
        
        return recipient
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении адреса для выставления счетов по умолчанию: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить адрес для выставления счетов по умолчанию")