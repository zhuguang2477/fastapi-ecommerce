# backend/app/services/user_service.py
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from backend.app.models.user import User
from backend.app.schemas.user import UserCreate, UserUpdate

logger = logging.getLogger(__name__)

# Контекст хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """Класс сервиса пользователей"""
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Генерация хеша пароля"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """Создание нового пользователя
        
        Args:
            db: Сессия базы данных
            user_data: Данные для создания пользователя
        
        Returns:
            User: Созданный объект пользователя
        """
        try:
            # Проверка существования email
            existing_user = db.query(User).filter(User.email == user_data.email).first()
            if existing_user:
                raise ValueError(f"Email {user_data.email} уже зарегистрирован")
            
            # Создание объекта пользователя
            user = User(
                email=user_data.email,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                # Пароль должен быть захэширован перед вызовом этого метода
                # Или обработать здесь: hashed_password=self.get_password_hash(user_data.password)
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info(f"Пользователь успешно создан: {user.email} (ID: {user.id})")
            return user
            
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка создания пользователя: {e}")
            raise
    
    @staticmethod
    def create_or_update_user(db: Session, email: str, **kwargs) -> User:
        """Создание или обновление пользователя (для процесса OTP-авторизации)
        
        Args:
            db: Сессия базы данных
            email: Email пользователя
            **kwargs: Другая информация о пользователе
        
        Returns:
            User: Объект пользователя
        """
        try:
            # Поиск существующего пользователя
            user = db.query(User).filter(User.email == email).first()
            
            if user:
                # Обновление информации пользователя
                for key, value in kwargs.items():
                    if hasattr(user, key) and value is not None:
                        setattr(user, key, value)
                
                user.is_verified = True  # Пометить как верифицированного после OTP
                db.commit()
                db.refresh(user)
                
                logger.info(f"Пользователь успешно обновлен: {email}")
            else:
                # Создание нового пользователя
                user = User(
                    email=email,
                    first_name=kwargs.get('first_name'),
                    last_name=kwargs.get('last_name'),
                    is_verified=True  # OTP верификация пройдена
                )
                
                db.add(user)
                db.commit()
                db.refresh(user)
                
                logger.info(f"Пользователь успешно создан: {email} (ID: {user.id})")
            
            return user
            
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка создания/обновления пользователя: {e}")
            raise
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Получение пользователя по email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Обновление информации пользователя"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                return None
            
            # Обновление полей
            if user_data.first_name is not None:
                user.first_name = user_data.first_name
            if user_data.last_name is not None:
                user.last_name = user_data.last_name
            if user_data.phone is not None:
                user.phone = user_data.phone
            if user_data.avatar_url is not None:
                user.avatar_url = user_data.avatar_url
            
            # Проверка статуса заполнения профиля
            user.check_profile_completion()
            
            db.commit()
            db.refresh(user)
            
            logger.info(f"Информация пользователя успешно обновлена: {user.email}")
            return user
            
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка обновления информации пользователя: {e}")
            raise
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Аутентификация пользователя
        
        Примечание: Этот метод предполагает, что пароль пользователя уже хранится в БД (в хэшированной форме)
        Если проект использует OTP-авторизацию, этот метод может не понадобиться
        """
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        # Проверка пароля (здесь нужна проверка по фактическому хэшу пароля в БД)
        # Предполагается, что пароль уже захэширован и хранится в базе данных
        # if not self.verify_password(password, user.hashed_password):
        #     return None
        
        return user