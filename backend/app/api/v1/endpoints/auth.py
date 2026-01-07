# backend/app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
from typing import Optional

from backend.app.database import get_db
from backend.app.schemas.auth import SendOTPRequest, ConfirmOTPRequest, CompleteProfileRequest
from backend.app.schemas.otp import TokenResponse, OTPStatusResponse
from backend.app.schemas.user import UserResponse
from backend.app.services.user_service import UserService
from backend.app.services.otp_service import OTPService
from backend.app.core.security import create_access_token, get_current_active_user
from backend.app.core.email import get_email_service
from backend.app.models.user import User
from backend.app.core.config import settings
from backend.app.core.cache import cache_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/send-otp",
    summary="Отправить OTP код",
    description="Отправить 6-значный код подтверждения на указанный email",
    response_model=dict
)
async def send_otp(
    request: Request,
    otp_request: SendOTPRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Запросить OTP код подтверждения
    
    - **email**: Email пользователя
    """
    try:
        # 1. Валидация формата email
        if not otp_request.email or '@' not in otp_request.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный формат email"
            )
        
        # 2. Проверка ограничения частоты запросов
        ip_address = request.client.host
        if not OTPService.can_send_otp(otp_request.email, ip_address, db):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Слишком много запросов, попробуйте позже"
            )
        
        # 3. Отправка OTP письма
        success = await OTPService.send_otp_email(otp_request.email, ip_address, db)
        
        if success:
            logger.info(f"OTP отправлен успешно: {otp_request.email}")
            
            # 4. Проверка существования пользователя
            user = UserService.get_user_by_email(db, otp_request.email)
            is_new_user = user is None
            
            response_data = {
                "message": "Код подтверждения отправлен на вашу почту",
                "email": otp_request.email,
                "success": True,
                "is_new_user": is_new_user
            }
            
            # 5. Если пользователь существует, вернуть дополнительную информацию
            if user:
                response_data.update({
                    "is_profile_completed": user.is_profile_completed,
                    "is_verified": user.is_verified
                })
            
            return response_data
        else:
            logger.error(f"Не удалось отправить OTP: {otp_request.email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не удалось отправить код подтверждения, попробуйте позже"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка отправки OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при отправке кода подтверждения: {str(e)}"
        )


@router.post(
    "/confirm-otp",
    response_model=TokenResponse,
    summary="Подтвердить OTP и войти",
    description="Подтвердить OTP код, создать сессию пользователя и вернуть JWT токен"
)
async def confirm_otp(
    request: Request,
    otp_verify: ConfirmOTPRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Подтвердить OTP код
    
    - **email**: Email пользователя
    - **otp_code**: 6-значный код подтверждения
    """
    try:
        ip_address = request.client.host
        
        # 1. Проверка OTP кода
        otp_record = OTPService.verify_otp(
            otp_verify.email, 
            otp_verify.otp_code, 
            ip_address,
            db
        )
        
        if not otp_record:
            # Проверка, не истек ли OTP
            last_otp = OTPService.get_last_otp(otp_verify.email, db)
            if last_otp and last_otp.expires_at < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Код подтверждения истек, запросите новый"
                )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный код подтверждения"
            )
        
        # 2. Получение или создание пользователя
        user = UserService.get_user_by_email(db, otp_verify.email)
        is_new_user = False
        
        if not user:
            # 3. Создание нового пользователя
            user = UserService.create_or_update_user(
                db=db,
                email=otp_verify.email,
                registration_ip=ip_address,
                is_verified=True,
                otp_enabled=True,
                otp_verified=True
            )
            is_new_user = True
            
            logger.info(f"Новый пользователь создан через OTP: {user.email} (ID: {user.id})")
        else:
            # 4. Обновление существующего пользователя
            user = UserService.update_otp_status(
                db=db,
                user_id=user.id,
                is_verified=True,
                otp_verified=True
            )
            
            logger.info(f"Пользователь вошел через OTP: {user.email} (ID: {user.id})")
        
        # 5. Пометить OTP как использованный
        user.last_login_ip = ip_address
        user.last_login_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        # 6. Запись активности входа
        UserService.record_login_activity(
            db=db,
            user_id=user.id,
            ip_address=ip_address,
            login_method="otp"
        )
        
        # 7. Создание JWT токена
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user.email, 
                "user_id": user.id,
                "login_ip": ip_address,
                "login_time": datetime.utcnow().isoformat()
            },
            expires_delta=access_token_expires
        )
        
        # 8. Очистка кэша
        cache_key = f"login_attempts:{ip_address}:{user.email}"
        await cache_service.delete(cache_key)
        
        # 9. Отправка приветственного письма (для новых пользователей)
        if is_new_user:
            email_service = get_email_service()
            background_tasks.add_task(
                email_service.send_welcome_email,
                user.email,
                user.first_name or user.email.split('@')[0]
            )
        
        # 10. Формирование ответа
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            is_verified=user.is_verified,
            is_active=user.is_active,
            is_profile_completed=user.is_profile_completed,
            otp_enabled=user.otp_enabled,
            otp_verified=user.otp_verified,
            avatar_url=user.avatar_url,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        otp_status = OTPStatusResponse(
            email=user.email,
            is_verified=user.is_verified,
            otp_enabled=user.otp_enabled,
            otp_verified=user.otp_verified,
            verification_expires_at=otp_record.expires_at,
            last_otp_sent_at=otp_record.created_at
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response.dict(),
            user_id=user.id,
            email=user.email,
            is_profile_completed=user.is_profile_completed,
            otp_status=otp_status
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка подтверждения OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при подтверждении: {str(e)}"
        )


@router.post(
    "/complete-profile",
    response_model=UserResponse,
    summary="Завершить регистрацию профиля",
    description="Завершить регистрацию профиля после OTP подтверждения"
)
async def complete_profile(
    profile_data: CompleteProfileRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Завершить регистрацию профиля
    
    - **first_name**: Имя (обязательно)
    - **last_name**: Фамилия (обязательно)
    - **phone**: Номер телефона (обязательно)
    """
    try:
        # 1. Проверка, завершен ли профиль
        if current_user.is_profile_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Профиль уже завершен"
            )
        
        # 2. Валидация входных данных
        if not all([profile_data.first_name, profile_data.last_name, profile_data.phone]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Все поля (имя, фамилия, телефон) обязательны"
            )
        
        # 3. Валидация формата телефона
        import re
        phone_pattern = re.compile(r'^\+?[1-9]\d{1,14}$')
        if not phone_pattern.match(profile_data.phone):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный формат номера телефона. Используйте международный формат"
            )
        
        # 4. Проверка, используется ли телефон другим пользователем
        existing_user = UserService.get_user_by_phone(db, profile_data.phone)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Этот номер телефона уже используется другим пользователем"
            )
        
        # 5. Обновление данных пользователя
        update_data = {
            'first_name': profile_data.first_name.strip(),
            'last_name': profile_data.last_name.strip(),
            'phone': profile_data.phone,
            'is_profile_completed': True,
            'profile_completed_at': datetime.utcnow()
        }
        
        user = UserService.update_user_profile(
            db=db, 
            user_id=current_user.id, 
            profile_data=update_data
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        logger.info(f"Завершена регистрация профиля: {user.email}")
        
        # 6. Отправка уведомления по email
        email_service = get_email_service()
        background_tasks.add_task(
            email_service.send_profile_completed_email,
            user.email,
            user.first_name
        )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            is_verified=user.is_verified,
            is_active=user.is_active,
            is_profile_completed=user.is_profile_completed,
            otp_enabled=user.otp_enabled,
            otp_verified=user.otp_verified,
            avatar_url=user.avatar_url,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка завершения профиля: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при завершении профиля"
        )


@router.get(
    "/profile",
    response_model=UserResponse,
    summary="Получить профиль пользователя",
    description="Получить информацию о текущем пользователе"
)
async def get_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить профиль текущего пользователя
    """
    try:
        return UserResponse(
            id=current_user.id,
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            phone=current_user.phone,
            is_verified=current_user.is_verified,
            is_active=current_user.is_active,
            is_profile_completed=current_user.is_profile_completed,
            otp_enabled=current_user.otp_enabled,
            otp_verified=current_user.otp_verified,
            avatar_url=current_user.avatar_url,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения профиля: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения профиля"
        )


@router.put(
    "/profile",
    response_model=UserResponse,
    summary="Обновить профиль пользователя",
    description="Обновить информацию профиля текущего пользователя"
)
async def update_profile(
    first_name: str = None,
    last_name: str = None,
    phone: str = None,
    avatar_url: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Обновить профиль пользователя
    
    - **first_name**: Имя (опционально)
    - **last_name**: Фамилия (опционально)
    - **phone**: Телефон (опционально)
    - **avatar_url**: URL аватара (опционально)
    """
    try:
        # Подготовить данные для обновления
        update_data = {}
        
        if first_name is not None:
            update_data['first_name'] = first_name
        
        if last_name is not None:
            update_data['last_name'] = last_name
        
        if phone is not None:
            import re
            phone_pattern = re.compile(r'^\+?[1-9]\d{1,14}$')
            if not phone_pattern.match(phone):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Неверный формат номера телефона. Используйте международный формат."
                )
            update_data['phone'] = phone
        
        if avatar_url is not None:
            update_data['avatar_url'] = avatar_url
        
        # Если нет данных для обновления
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не предоставлены данные для обновления"
            )
        
        # Обновить пользователя
        user = UserService.update_user_profile(
            db=db,
            user_id=current_user.id,
            profile_data=update_data
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        logger.info(f"Профиль пользователя обновлен: {user.email}")
        
        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            is_verified=user.is_verified,
            is_active=user.is_active,
            is_profile_completed=user.is_profile_completed,
            otp_enabled=user.otp_enabled,
            otp_verified=user.otp_verified,
            avatar_url=user.avatar_url,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обновления профиля: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка обновления профиля"
        )


@router.post(
    "/logout",
    summary="Выход из системы",
    description="Завершение сеанса пользователя",
    response_model=dict
)
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """
    Выход из системы
    
    Примечание: В JWT-аутентификации выход реализуется на клиенте
    путем удаления токена. Этот endpoint предоставляет формальный
    способ завершения сеанса.
    """
    try:
        logger.info(f"Пользователь вышел из системы: {current_user.email}")
        
        return {
            "message": "Успешный выход из системы",
            "success": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка выхода из системы: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка выхода из системы"
        )


@router.post(
    "/refresh-token",
    summary="Обновить токен",
    description="Обновить истекший токен доступа",
    response_model=dict
)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Обновить токен доступа
    
    - **refresh_token**: Refresh токен
    """
    try:
        # Проверить refresh токен
        # Реализация зависит от вашей стратегии refresh токенов
        
        # Временная реализация - возвращаем ошибку
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Обновление токена еще не реализовано"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обновления токена: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка обновления токена"
        )


@router.post(
    "/enable-otp",
    summary="Включить OTP двухфакторную аутентификацию",
    description="Включить OTP для дополнительной безопасности",
    response_model=dict
)
async def enable_otp(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Включить OTP двухфакторную аутентификацию
    """
    try:
        # Проверить, что пользователь уже верифицирован
        if not current_user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Сначала подтвердите свой email через OTP"
            )
        
        # Включить OTP
        user = UserService.update_otp_status(
            db=db,
            user_id=current_user.id,
            otp_enabled=True
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        logger.info(f"OTP включен для пользователя: {user.email}")
        
        return {
            "message": "OTP двухфакторная аутентификация включена",
            "success": True,
            "otp_enabled": user.otp_enabled,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка включения OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка включения OTP"
        )


@router.post(
    "/disable-otp",
    summary="Отключить OTP двухфакторную аутентификацию",
    description="Отключить OTP для упрощения входа",
    response_model=dict
)
async def disable_otp(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Отключить OTP двухфакторную аутентификацию
    """
    try:
        # Отключить OTP
        user = UserService.update_otp_status(
            db=db,
            user_id=current_user.id,
            otp_enabled=False
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        logger.info(f"OTP отключен для пользователя: {user.email}")
        
        return {
            "message": "OTP двухфакторная аутентификация отключена",
            "success": True,
            "otp_enabled": user.otp_enabled,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка отключения OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка отключения OTP"
        )