# backend/app/api/v1/endpoints/shops.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from backend.app.database import get_db
from backend.app.schemas.shop import (
    ShopCreate, ShopJoinRequest, ShopResponse,
    ShopMemberResponse, ShopUpdate, ShopAdminSettings
)
from backend.app.services.shop_service import ShopService
from backend.app.core.security import get_current_active_user
from backend.app.models.user import User
from backend.app.models.shop import Shop, ShopMember
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/",
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
    "/my-shops",
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
    "/join",
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
    "/my-shops/pending-requests",  # 改为 /my-shops/pending-requests
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
    "/{shop_id}/approve-request",
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
    "/{shop_id}/members",
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
    

@router.get(
    "/{shop_id}",
    response_model=ShopResponse,
    summary="Получить информацию о магазине",
    description="Получить детальную информацию о конкретном магазине"
)
async def get_shop(
    shop_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить информацию о магазине"""
    try:
        # Проверить, имеет ли пользователь доступ к магазину
        member = db.query(ShopMember).filter(
            ShopMember.shop_id == shop_id,
            ShopMember.user_id == current_user.id,
            ShopMember.is_approved == True
        ).first()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет доступа к этому магазину"
            )
        
        shop = db.query(Shop).filter(Shop.id == shop_id).first()
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Магазин не найден"
            )
        
        return shop
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении информации о магазине: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить информацию о магазине"
        )


@router.put(
    "/{shop_id}",
    response_model=ShopResponse,
    summary="Обновить информацию о магазине",
    description="Обновить основную информацию о магазине"
)
async def update_shop(
    shop_id: int,
    shop_data: ShopUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Обновить информацию о магазине"""
    try:
        # Проверить, является ли пользователь владельцем магазина
        shop = db.query(Shop).filter(
            Shop.id == shop_id,
            Shop.owner_id == current_user.id
        ).first()
        
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только владелец может обновлять информацию о магазине"
            )
        
        # Обновить поля магазина
        for key, value in shop_data.dict(exclude_unset=True).items():
            setattr(shop, key, value)
        
        shop.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(shop)
        
        logger.info(f"Пользователь {current_user.id} обновил магазин {shop_id}")
        
        return shop
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при обновлении магазина: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось обновить информацию о магазине"
        )


@router.delete(
    "/{shop_id}",
    summary="Удалить магазин",
    description="Удалить магазин (только для владельца)"
)
async def delete_shop(
    shop_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Удалить магазин"""
    try:
        # Проверить, является ли пользователь владельцем магазина
        shop = db.query(Shop).filter(
            Shop.id == shop_id,
            Shop.owner_id == current_user.id
        ).first()
        
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только владелец может удалить магазин"
            )
        
        # Проверить, есть ли активные заказы
        from backend.app.models.order import Order
        active_orders = db.query(Order).filter(
            Order.shop_id == shop_id,
            Order.status.notin_(["completed", "cancelled"])
        ).count()
        
        if active_orders > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Невозможно удалить магазин с активными заказами"
            )
        
        # Мягкое удаление (изменение статуса)
        shop.is_active = False
        shop.deleted_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Пользователь {current_user.id} удалил магазин {shop_id}")
        
        return {"message": "Магазин успешно удален"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при удалении магазина: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось удалить магазин"
        )


@router.post(
    "/{shop_id}/admin-settings",
    summary="Обновить административные настройки магазина",
    description="Настройки, доступные только администраторам"
)
async def update_admin_settings(
    shop_id: int,
    admin_settings: ShopAdminSettings,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Обновить административные настройки магазина"""
    try:
        # Проверить, является ли пользователь администратором магазина
        member = db.query(ShopMember).filter(
            ShopMember.shop_id == shop_id,
            ShopMember.user_id == current_user.id,
            ShopMember.is_approved == True,
            ShopMember.role.in_(["admin", "owner"])
        ).first()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Требуются права администратора"
            )
        
        # Обновить настройки
        shop = db.query(Shop).filter(Shop.id == shop_id).first()
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Магазин не найден"
            )
        
        # Обновить поля настроек
        for key, value in admin_settings.dict(exclude_unset=True).items():
            setattr(shop, key, value)
        
        db.commit()
        db.refresh(shop)
        
        logger.info(f"Администратор {current_user.id} обновил настройки магазина {shop_id}")
        
        return {"message": "Административные настройки обновлены"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при обновлении административных настроек: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось обновить административные настройки"
        )