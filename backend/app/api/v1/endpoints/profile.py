# backend/app/api/v1/endpoints/profile.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from backend.app.database import get_db
from backend.app.schemas.profile import ProfileUpdate, ProfileResponse
from backend.app.services.user_service import UserService
from backend.app.core.security import get_current_active_user, get_current_user
from backend.app.models.user import User


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/me/profile",
    response_model=ProfileResponse,
    summary="Доступ к личным данным",
    description="Получение личных данных текущего пользователя"
)
async def get_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получение личных данных текущего пользователя"""
    user = UserService.get_user_profile(db, current_user.id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    return user


@router.patch(
    "/me/profile",
    response_model=ProfileResponse,
    summary="Обновление личных данных",
    description="Обновить личные данные текущего пользователя"
)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Обновление личных данных пользователей"""
    try:
        updated_user = UserService.update_profile(
            db, current_user.id, profile_data
        )
        
        logger.info(f"Успешное обновление профиля пользователя: {current_user.id}")
        return updated_user
        
    except Exception as e:
        logger.error(f"Ошибка обновления личных данных: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обновления личных данных: {str(e)}"
        )
    
@router.patch("/me/profile", response_model=ProfileResponse)
async def update_profile(
    profile_update: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление профиля"""
    try:
        update_data = profile_update.dict(exclude_unset=True)
        
        # Проверка наличия данных для обновления
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не предоставлены данные для обновления"
            )
        
        # Обновление информации о пользователе
        for field, value in update_data.items():
            setattr(current_user, field, value)
        
        # Проверка полноты профиля
        if current_user.first_name and current_user.last_name:
            current_user.is_profile_completed = True
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"Обновление профиля пользователя: {current_user.email}")
        
        return ProfileResponse(
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            full_name=current_user.first_name + " " + current_user.last_name 
                if current_user.first_name and current_user.last_name 
                else current_user.first_name or current_user.last_name,
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
            detail="Не удалось обновить данные, попробуйте позже"
        )