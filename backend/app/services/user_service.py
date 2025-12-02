# backend/app/services/user_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional
from datetime import datetime

from backend.app.models.user import User
from backend.app.schemas.user import UserCreate, UserUpdate
from backend.app.schemas.profile import ProfileUpdate
import logging

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Доступ к пользователям через почтовый ящик"""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Получение пользователей с помощью ID"""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create_or_update_user(db: Session, email: str) -> User:
        """
        Создать или обновить пользователя
        
        Args:
            db: Сеанс базы данных
            email: Почтовый ящик пользователя
            
        Returns:
            User: Создать или обновить объект пользователя
        """
        # Проверьте, существует ли пользователь
        existing_user = UserService.get_user_by_email(db, email)
        
        if existing_user:
            # Обновление существующих пользователей
            existing_user.is_verified = True
            existing_user.last_login = datetime.utcnow()
            db.commit()
            db.refresh(existing_user)
            
            logger.info(f"Updated existing user: {email}")
            return existing_user
        else:
            # Создание новых пользователей
            db_user = User(
                email=email,
                is_verified=True,
                last_login=datetime.utcnow(),
                is_profile_completed=False
            )
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            logger.info(f"Created new user: {email}, ID: {db_user.id}")
            return db_user
    
    @staticmethod
    def update_profile(db: Session, user_id: int, profile_data: ProfileUpdate) -> User:
        """
        Обновление личных данных пользователей
        
        Args:
            db: Сеанс базы данных
            user_id: Идентификатор пользователя
            profile_data: Персональные данные
            
        Returns:
            User: Обновленные пользователи
        """
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Обновить поле
        update_data = profile_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        # Проверьте, завершены ли личные данные
        if user.first_name and user.last_name:
            user.is_profile_completed = True
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"Updated profile for user {user_id}")
        return user
    
    @staticmethod
    def get_user_profile(db: Session, user_id: int) -> Optional[User]:
        """Доступ к персональным данным пользователей"""
        return db.query(User).filter(User.id == user_id).first()