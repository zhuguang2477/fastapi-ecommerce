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
    description="Создайте новый магазин, где текущие пользователи станут владельцами"
)
async def create_shop(
    shop_data: ShopCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Создать новый магазин"""
    try:
        # Убедитесь, что пользователь усовершенствовал свои личные данные
        if not current_user.is_profile_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Сначала уточните свой профиль."
            )
        
        shop = ShopService.create_shop(db, current_user.id, shop_data)
        return shop
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка создания магазина: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания магазина: {str(e)}"
        )


@router.get(
    "/me/shops",
    response_model=List[ShopResponse],
    summary="Купить мой магазин",
    description="Получите доступ ко всем магазинам, принадлежащим текущим пользователям или присоединившимся к ним"
)
async def get_my_shops(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить список магазинов пользователей"""
    shops = ShopService.get_user_shops(db, current_user.id)
    return shops


@router.post(
    "/shops/join",
    summary="Присоединяйтесь к существующим магазинам",
    description="Присоединяйтесь к существующему магазину через пароль (нужно дождаться одобрения владельца)"
)
async def join_shop(
    join_request: ShopJoinRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Присоединяйтесь к магазинам"""
    try:
        # Убедитесь, что пользователь усовершенствовал свои личные данные
        if not current_user.is_profile_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Сначала уточните свой профиль."
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
        logger.error(f"Сбой в магазине: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Сбой в магазине: {str(e)}"
        )


@router.get(
    "/me/shops/pending-requests",
    response_model=List[ShopMemberResponse],
    summary="Получение необработанных запросов",
    description="Получение необработанных запросов на присоединение в магазине, принадлежащем текущему пользователю"
)
async def get_pending_requests(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получение необработанных запросов"""
    requests = ShopService.get_pending_requests(db, current_user.id)
    
    # Построить данные ответа
    response_data = []
    for req in requests:
        user = db.query(User).filter(User.id == req.user_id).first()
        response_data.append({
            "id": req.id,
            "shop_id": req.shop_id,
            "user_id": req.user_id,
            "user_email": user.email if user else "Unknown",
            "user_full_name": f"{user.last_name} {user.first_name}" if user and user.first_name and user.last_name else user.email if user else "Unknown",
            "role": req.role,
            "is_approved": req.is_approved,
            "created_at": req.created_at
        })
    
    return response_data


@router.post(
    "/shops/{shop_id}/approve-request",
    summary="Удовлетворение просьб о присоединении",
    description="Одобрение или отклонение заявки пользователя на вступление в магазин"
)
async def approve_request(
    shop_id: int,
    request_id: int,
    approve: bool = True,
    role: str = "viewer",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Ратификация или отклонение просьб о присоединении"""
    try:
        # Проверьте, является ли текущий пользователь владельцем магазина
        shop = db.query(Shop).filter(
            Shop.id == shop_id,
            Shop.owner_id == current_user.id
        ).first()
        
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы не являетесь владельцем магазина."
            )
        
        result = ShopService.approve_request(db, request_id, approve, role)
        
        if approve:
            return {
                "message": "Просьба удовлетворена",
                "request_id": request_id,
                "approved": True
            }
        else:
            return {
                "message": "Просьба отклонена.",
                "request_id": request_id,
                "approved": False
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обработки запроса: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обработки запроса: {str(e)}"
        )


@router.get(
    "/shops/{shop_id}/members",
    response_model=List[ShopMemberResponse],
    summary="Приобретение членов магазина",
    description="Получить список всех членов указанного магазина"
)
async def get_shop_members(
    shop_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Приобретение членов магазина"""
    try:
        # Проверьте, есть ли у пользователя права на просмотр членов
        member = db.query(ShopMember).filter(
            ShopMember.shop_id == shop_id,
            ShopMember.user_id == current_user.id,
            ShopMember.is_approved == True
        ).first()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав на просмотр членов магазина."
            )
        
        members = ShopService.get_shop_members(db, shop_id)
        
        # Построить данные ответа
        response_data = []
        for member in members:
            user = db.query(User).filter(User.id == member.user_id).first()
            response_data.append({
                "id": member.id,
                "shop_id": member.shop_id,
                "user_id": member.user_id,
                "user_email": user.email if user else "Unknown",
                "user_full_name": f"{user.last_name} {user.first_name}" if user and user.first_name and user.last_name else user.email if user else "Unknown",
                "role": member.role,
                "is_approved": member.is_approved,
                "created_at": member.created_at
            })
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Сбой с членами магазина: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Сбой с членами магазина: {str(e)}"
        )