# backend/app/api/v1/endpoints/shops.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.app.database import get_db
from backend.app.schemas.shop import (
    ShopCreate, ShopJoinRequest, ShopResponse,
    ShopMemberResponse
)
from backend.app.services.shop_service import ShopService
from backend.app.core.security import get_current_active_user
from backend.app.models.user import User
from backend.app.models.shop import Shop, ShopMember
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/shops",
    response_model=ShopResponse,
    summary="Создать новый магазин",
    description="Создание нового магазина, текущий пользователь становится владельцем"
)
async def create_shop(
    shop_data: ShopCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Создать новый магазин"""
    try:
        # Проверить, заполнил ли пользователь свой профиль
        if not current_user.is_profile_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Сначала заполните свой профиль."
            )
        
        shop = ShopService.create_shop(db, current_user.id, shop_data)
        return shop
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при создании магазина: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании магазина: {str(e)}"
        )


@router.get(
    "/me/shops",
    response_model=List[ShopResponse],
    summary="Получить мои магазины",
    description="Получить все магазины, которыми владеет или в которых участвует текущий пользователь"
)
async def get_my_shops(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить список магазинов пользователя"""
    shops = ShopService.get_user_shops(db, current_user.id)
    return shops


@router.post(
    "/shops/join",
    summary="Присоединиться к существующему магазину",
    description="Присоединение к существующему магазину по паролю (требуется одобрение владельца)"
)
async def join_shop(
    join_request: ShopJoinRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Присоединиться к магазину"""
    try:
        # Проверить, заполнил ли пользователь свой профиль
        if not current_user.is_profile_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Сначала заполните свой профиль."
            )
        
        member = ShopService.join_shop(db, current_user.id, join_request.join_password)
        
        return {
            "message": "Запрос на присоединение отправлен и ожидает одобрения владельца магазина",
            "shop_id": member.shop_id,
            "request_id": member.id,
            "status": "pending"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при присоединении к магазину: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при присоединении к магазину: {str(e)}"
        )


@router.get(
    "/me/shops/pending-requests",
    response_model=List[ShopMemberResponse],
    summary="Получить ожидающие запросы",
    description="Получить ожидающие запросы на присоединение к магазинам, принадлежащим текущему пользователю"
)
async def get_pending_requests(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить ожидающие запросы"""
    requests = ShopService.get_pending_requests(db, current_user.id)
    
    # Построить данные для ответа
    response_data = []
    for req in requests:
        user = db.query(User).filter(User.id == req.user_id).first()
        response_data.append({
            "id": req.id,
            "shop_id": req.shop_id,
            "user_id": req.user_id,
            "user_email": user.email if user else "Неизвестно",
            "user_full_name": f"{user.last_name} {user.first_name}" if user and user.first_name and user.last_name else user.email if user else "Неизвестно",
            "role": req.role,
            "is_approved": req.is_approved,
            "created_at": req.created_at
        })
    
    return response_data


@router.post(
    "/shops/{shop_id}/approve-request",
    summary="Обработать запрос на присоединение",
    description="Одобрить или отклонить запрос пользователя на присоединение к магазину"
)
async def approve_request(
    shop_id: int,
    request_id: int,
    approve: bool = True,
    role: str = "viewer",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Одобрить или отклонить запрос на присоединение"""
    try:
        # Проверить, является ли текущий пользователь владельцем магазина
        shop = db.query(Shop).filter(
            Shop.id == shop_id,
            Shop.owner_id == current_user.id
        ).first()
        
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы не являетесь владельцем этого магазина."
            )
        
        result = ShopService.approve_request(db, request_id, approve, role)
        
        if approve:
            return {
                "message": "Запрос одобрен",
                "request_id": request_id,
                "approved": True
            }
        else:
            return {
                "message": "Запрос отклонен",
                "request_id": request_id,
                "approved": False
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обработке запроса: {str(e)}"
        )


@router.get(
    "/shops/{shop_id}/members",
    response_model=List[ShopMemberResponse],
    summary="Получить участников магазина",
    description="Получить список всех участников указанного магазина"
)
async def get_shop_members(
    shop_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить участников магазина"""
    try:
        # Проверить, есть ли у пользователя право просматривать участников
        member = db.query(ShopMember).filter(
            ShopMember.shop_id == shop_id,
            ShopMember.user_id == current_user.id,
            ShopMember.is_approved == True
        ).first()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав для просмотра участников магазина."
            )
        
        members = ShopService.get_shop_members(db, shop_id)
        
        # Построить данные для ответа
        response_data = []
        for member in members:
            user = db.query(User).filter(User.id == member.user_id).first()
            response_data.append({
                "id": member.id,
                "shop_id": member.shop_id,
                "user_id": member.user_id,
                "user_email": user.email if user else "Неизвестно",
                "user_full_name": f"{user.last_name} {user.first_name}" if user and user.first_name and user.last_name else user.email if user else "Неизвестно",
                "role": member.role,
                "is_approved": member.is_approved,
                "created_at": member.created_at
            })
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении участников магазина: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении участников магазина: {str(e)}"
        )