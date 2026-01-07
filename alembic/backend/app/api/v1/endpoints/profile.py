# backend/app/api/v1/endpoints/profile.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from backend.app.database import get_db
from backend.app.schemas.profile import ProfileUpdate, ProfileResponse
from backend.app.services.user_service import UserService
from backend.app.core.security import get_current_active_user
from backend.app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/profile",
    response_model=ProfileResponse,
    summary="Получить профиль",
    description="Получить профиль текущего пользователя"
)
async def get_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить профиль"""
    try:
        # Непосредственно возвращаем информацию о текущем пользователе в формате ProfileResponse
        return ProfileResponse(
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            full_name=f"{current_user.first_name or ''} {current_user.last_name or ''}".strip() or None,
            phone=current_user.phone,
            avatar_url=current_user.avatar_url,
            is_verified=current_user.is_verified,
            is_profile_completed=current_user.is_profile_completed,
            created_at=current_user.created_at
        )
    except Exception as e:
        logger.error(f"Ошибка получения профиля: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить профиль"
        )


@router.put(
    "/profile",
    response_model=ProfileResponse,
    summary="Обновить профиль",
    description="Обновить профиль текущего пользователя"
)
async def update_profile(
    profile_update: ProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Обновить профиль"""
    try:
        update_data = profile_update.dict(exclude_unset=True)
        
        # Проверить, есть ли данные для обновления
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Данные для обновления не предоставлены"
            )
        
        # Проверить и обновить поля
        if 'first_name' in update_data:
            current_user.first_name = update_data['first_name']
        if 'last_name' in update_data:
            current_user.last_name = update_data['last_name']
        if 'phone' in update_data:
            current_user.phone = update_data['phone']
        if 'avatar_url' in update_data:
            current_user.avatar_url = update_data['avatar_url']
        
        # Проверить, заполнен ли профиль
        current_user.is_profile_completed = bool(
            current_user.first_name and 
            current_user.last_name and 
            current_user.phone
        )
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"Профиль пользователя обновлен: {current_user.email}")
        
        return ProfileResponse(
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            full_name=f"{current_user.first_name or ''} {current_user.last_name or ''}".strip() or None,
            phone=current_user.phone,
            avatar_url=current_user.avatar_url,
            is_verified=current_user.is_verified,
            is_profile_completed=current_user.is_profile_completed,
            created_at=current_user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка обновления профиля: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось обновить профиль"
        )