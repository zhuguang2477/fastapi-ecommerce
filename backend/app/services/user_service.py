# backend/app/services/user_service.py
"""
Сервис пользователей
"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from backend.app.models.user import User
from backend.app.core.security import get_password_hash

logger = logging.getLogger(__name__)


class UserService:
    """Класс сервиса пользователей"""
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Получить пользователя по email"""
        try:
            return db.query(User).filter(User.email == email).first()
        except Exception as e:
            logger.error(f"Ошибка получения пользователя: {e}")
            return None
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        try:
            return db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"Ошибка получения пользователя: {e}")
            return None
    
    @staticmethod
    def create_or_update_user(
        db: Session,
        email: str,
        is_verified: bool = False,
        otp_enabled: bool = False,
        otp_verified: bool = False,
        registration_ip: Optional[str] = None,
        **kwargs  # 接收其他可选参数
    ) -> Optional[User]:
        """Создать или обновить пользователя"""
        try:
            # Проверить, существует ли пользователь
            user = db.query(User).filter(User.email == email).first()
            
            if user:
                # Обновить существующего пользователя
                user.is_verified = is_verified
                user.otp_enabled = otp_enabled
                user.otp_verified = otp_verified
                user.updated_at = datetime.now()
            else:
                # Создать нового пользователя
                user = User(
                    email=email,
                    is_verified=is_verified,
                    otp_enabled=otp_enabled,
                    otp_verified=otp_verified,
                    is_active=True,
                    registration_ip=registration_ip,
                    login_count=0  # 初始化登录次数
                )
                db.add(user)
            
            db.commit()
            db.refresh(user)
            
            logger.info(f"Пользователь создан/обновлен успешно: {email}")
            return user
            
        except IntegrityError as e:
            logger.error(f"Ошибка создания/обновления пользователя (нарушение целостности): {e}")
            db.rollback()
            return None
        except Exception as e:
            logger.error(f"Ошибка создания/обновления пользователя: {e}")
            db.rollback()
            return None
        
    @staticmethod
    def get_user_by_phone(db: Session, phone: str) -> Optional[User]:
        """Получить пользователя по телефону"""
        try:
            return db.query(User).filter(User.phone == phone).first()
        except Exception as e:
            logger.error(f"Ошибка получения пользователя по телефону: {e}")
            return None
    
    @staticmethod
    def update_otp_status(
        db: Session,
        user_id: int,
        is_verified: bool = None,
        otp_enabled: bool = None,
        otp_verified: bool = None
    ) -> Optional[User]:
        """Обновить статус OTP пользователя"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"Пользователь не существует: {user_id}")
                return None
            
            # Обновить поля
            if is_verified is not None:
                user.is_verified = is_verified
            
            if otp_enabled is not None:
                user.otp_enabled = otp_enabled
            
            if otp_verified is not None:
                user.otp_verified = otp_verified
            
            user.updated_at = datetime.now()
            db.commit()
            db.refresh(user)
            
            logger.info(f"Статус OTP пользователя обновлен успешно: {user.email}")
            return user
            
        except Exception as e:
            logger.error(f"Ошибка обновления статуса OTP пользователя: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def update_user_profile(
        db: Session,
        user_id: int,
        profile_data: Dict[str, Any]
    ) -> Optional[User]:
        """Обновить профиль пользователя"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"Пользователь не существует: {user_id}")
                return None
            
            # Обновить поля
            for key, value in profile_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            # Если указаны имя и фамилия, отметить профиль как завершенный
            if 'first_name' in profile_data and 'last_name' in profile_data:
                user.is_profile_completed = True
            
            user.updated_at = datetime.now()
            db.commit()
            db.refresh(user)
            
            logger.info(f"Профиль пользователя обновлен успешно: {user.email}")
            return user
            
        except Exception as e:
            logger.error(f"Ошибка обновления профиля пользователя: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def deactivate_user(db: Session, user_id: int) -> bool:
        """Деактивировать пользователя"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"Пользователь не существует: {user_id}")
                return False
            
            user.is_active = False
            user.updated_at = datetime.now()
            db.commit()
            
            logger.info(f"Пользователь деактивирован: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка деактивации пользователя: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def activate_user(db: Session, user_id: int) -> bool:
        """Активировать пользователя"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"Пользователь не существует: {user_id}")
                return False
            
            user.is_active = True
            user.updated_at = datetime.now()
            db.commit()
            
            logger.info(f"Пользователь активирован: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка активации пользователя: {e}")
            db.rollback()
            return False
        
    @staticmethod
    def record_login_activity(
        db: Session,
        user_id: int,
        ip_address: str,
        user_agent: Optional[str] = None,
        login_method: str = "otp"
    ) -> bool:
        """记录用户登录活动（简化版）"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"用户不存在: {user_id}")
                return False
            
            # 只更新用户表中的信息
            user.last_login_at = datetime.now()
            user.last_login_ip = ip_address
            user.login_count = (user.login_count or 0) + 1
            
            db.commit()
            
            logger.info(f"用户登录记录: {user.email}, IP: {ip_address}, 方法: {login_method}")
            return True
            
        except Exception as e:
            logger.error(f"记录登录活动失败: {e}")
            db.rollback()
            return False