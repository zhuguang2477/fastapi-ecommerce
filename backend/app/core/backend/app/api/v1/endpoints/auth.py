# backend/app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import timedelta

from backend.app.database import get_db
from backend.app.schemas.auth import SendOTPRequest, ConfirmOTPRequest, RegisterRequest
from backend.app.schemas.otp import TokenResponse
from backend.app.schemas.user import UserResponse, Token
from backend.app.services.user_service import UserService
from backend.app.services.otp_service import OTPService
from backend.app.core.security import create_access_token
from backend.app.core.email import get_email_service
from backend.app.core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/send-otp",
    summary="Отправить код аутентификации OTP",
    description="Отправить 6-значный цифровой код на указанный почтовый ящик"
)
async def send_otp(
    otp_request: SendOTPRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Запросить код аутентификации OTP
    
    - **email**: Адрес электронной почты пользователя
    """
    try:
        # Отправить OTP по электронной почте
        success = await OTPService.send_otp_email(otp_request.email, db)
        
        if success:
            logger.info(f"Отправка OTP успешна: {otp_request.email}")
            return {
                "message": "Код подтверждения отправлен на ваш почтовый ящик.",
                "email": otp_request.email,
                "success": True
            }
        else:
            logger.error(f"Ошибка отправки OTP: {otp_request.email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось отправить проверочный код, попробуйте позже"
            )
            
    except Exception as e:
        logger.error(f"Ошибка отправки OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при отправке проверочного кода: {str(e)}"
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
    - **otp_code**: 6-значный проверочный код
    """
    try:
        # Проверить код OTP
        is_valid = OTPService.verify_otp(otp_verify.email, otp_verify.otp_code, db)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Код проверки недействителен или истек"
            )
        
        # Создать или обновить пользователя
        user = UserService.create_or_update_user(db, otp_verify.email)
        
        # Создание токенов JWT
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )
        
        logger.info(f"Пользователь успешно вошел в систему: {user.email}, ID: {user.id}")
        
        # Создать ответ пользователя
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_verified=user.is_verified,
            is_active=user.is_active,
            is_profile_completed=user.is_profile_completed,
            created_at=user.created_at
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка проверки OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка в процессе проверки: {str(e)}"
        )


@router.post(
    "/register",
    response_model=TokenResponse,
    summary="Регистрация пользователя",
    description="Регистрация пользователя и создание учетной записи"
)
async def register(
    register_data: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Регистрация пользователя
    
    - **email**: Почта пользователя
    - **password**: Пароль
    - **first_name**: Имя (опционально)
    - **last_name**: Фамилия (опционально)
    """
    try:
        # Создать пользователя
        user = UserService.create_user(
            db,
            register_data.email,
            register_data.password,
            register_data.first_name,
            register_data.last_name
        )
        
        # Создать JWT токен
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )
        
        # Отправить приветственное письмо
        email_service = get_email_service()
        background_tasks.add_task(
            email_service.send_welcome_email,
            user.email,
            user.first_name or user.email.split('@')[0]
        )
        
        logger.info(f"Пользователь успешно зарегистрирован: {user.email}")
        
        # Создать ответ пользователя
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_verified=user.is_verified,
            is_active=user.is_active,
            is_profile_completed=user.is_profile_completed,
            created_at=user.created_at
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Ошибка регистрации: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка регистрации, пожалуйста, попробуйте позже"
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Вход по паролю",
    description="Вход с использованием почты и пароля"
)
async def login(
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    """
    Вход по паролю
    
    - **email**: Почта пользователя
    - **password**: Пароль
    """
    try:
        # Проверить учетные данные пользователя
        user = UserService.authenticate_user(db, email, password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверная почта или пароль"
            )
        
        # Проверить, активен ли пользователь
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Учетная запись отключена"
            )
        
        # Создать JWT токен
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )
        
        logger.info(f"Вход по паролю успешен: {user.email}")
        
        # Создать ответ пользователя
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_verified=user.is_verified,
            is_active=user.is_active,
            is_profile_completed=user.is_profile_completed,
            created_at=user.created_at
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка входа: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка входа, пожалуйста, попробуйте позже"
        )