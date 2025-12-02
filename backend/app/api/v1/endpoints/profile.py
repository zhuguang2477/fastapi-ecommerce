# backend/app/api/v1/endpoints/profile.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.profile import ProfileUpdate, ProfileResponse
from backend.app.services.user_service import UserService
from backend.app.core.security import get_current_active_user
from backend.app.models.user import User
import logging

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
            detail="User not found"
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