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
    summary="获取个人资料",
    description="获取当前用户的个人资料"
)
async def get_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取个人资料"""
    try:
        # 直接返回当前用户信息，转换为ProfileResponse格式
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
        logger.error(f"获取个人资料错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="无法获取个人资料"
        )


@router.put(
    "/profile",
    response_model=ProfileResponse,
    summary="更新个人资料",
    description="更新当前用户的个人资料"
)
async def update_profile(
    profile_update: ProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新个人资料"""
    try:
        update_data = profile_update.dict(exclude_unset=True)
        
        # 检查是否有数据需要更新
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未提供更新数据"
            )
        
        # 验证和更新字段
        if 'first_name' in update_data:
            current_user.first_name = update_data['first_name']
        if 'last_name' in update_data:
            current_user.last_name = update_data['last_name']
        if 'phone' in update_data:
            current_user.phone = update_data['phone']
        if 'avatar_url' in update_data:
            current_user.avatar_url = update_data['avatar_url']
        
        # 检查资料是否完整
        current_user.is_profile_completed = bool(
            current_user.first_name and 
            current_user.last_name and 
            current_user.phone
        )
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"用户资料已更新: {current_user.email}")
        
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
        logger.error(f"更新个人资料错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新个人资料失败"
        )