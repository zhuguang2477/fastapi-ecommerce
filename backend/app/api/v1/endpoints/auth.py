# backend/app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import timedelta

from backend.app.database import get_db
from backend.app.schemas.auth import SendOTPRequest, ConfirmOTPRequest
from backend.app.schemas.otp import TokenResponse
from backend.app.services.user_service import UserService
from backend.app.services.otp_service import OTPService
from backend.app.core.security import create_access_token
from backend.app.core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/send-otp",
    summary="Отправить код аутентификации OTP",
    description="Отправить 6 - битный цифровой код на указанный почтовый ящик"
)
async def send_otp(
    otp_request: SendOTPRequest,
    background_tasks: BackgroundTasks,
):
    """
    Запросить код аутентификации OTP
    
    - **email**: Адрес электронной почты пользователя
    """
    try:
        # Отправить OTP - почту
        success = await OTPService.send_otp_email(otp_request.email)
        
        if success:
            logger.info(f"Отправить OTP успешно: {otp_request.email}")
            return {
                "message": "Код аутентификации OTP отправлен на ваш почтовый ящик",
                "email": otp_request.email,
                "success": True
            }
        else:
            logger.error(f"Ошибка отправки OTP: {otp_request.email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось отправить код проверки, попробуйте позже"
            )
            
    except Exception as e:
        logger.error(f"Ошибка при отправке OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка отправки кода проверки: {str(e)}"
        )


@router.post(
    "/confirm-otp",
    response_model=TokenResponse,
    summary="Проверить OTP и войти",
    description="Проверка кода OTP, создание сеанса пользователя и возвращение токена JWT"
)
async def confirm_otp(
    otp_verify: ConfirmOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Проверить код OTP
    
    - **email**: Адрес электронной почты пользователя
    - **otp**: 6 - битный код проверки
    """
    try:
        # Проверить код OTP
        is_valid = OTPService.verify_otp(otp_verify.email, otp_verify.otp)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный код или код истек"
            )
        
        # Создать или обновить пользователя
        user = UserService.create_or_update_user(db, otp_verify.email)
        
        # Создание токенов JWT
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )
        
        logger.info(f"Пользователь успешно вошел в систему: {user.email}, ID: {user.id}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id,
            email=user.email,
            is_profile_completed=user.is_profile_completed
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка проверки OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка в процессе проверки: {str(e)}"
        )