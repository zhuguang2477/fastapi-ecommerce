# 更新backend/app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field, validator, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
import re

class UserBase(BaseModel):
    """Базовая информация о пользователе"""
    email: EmailStr = Field(..., description="Электронная почта пользователя")
    first_name: Optional[str] = Field(None, max_length=50, description="Имя")
    last_name: Optional[str] = Field(None, max_length=50, description="Фамилия")
    
    @property
    def full_name(self) -> Optional[str]:
        """Вычисляет полное имя"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return None
    
    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    """Схема для создания пользователя"""
    password: str = Field(..., min_length=8, max_length=128, description="Пароль")
    
    @validator('password')
    def validate_password(cls, v):
        """Проверка сложности пароля"""
        if len(v) < 8:
            raise ValueError('Длина пароля должна быть не менее 8 символов')
        if v.isdigit():
            raise ValueError('Пароль не может состоять только из цифр')
        if v.isalpha():
            raise ValueError('Пароль должен содержать буквы и цифры')
        # Проверка на наличие специальных символов
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Пароль должен содержать хотя бы один специальный символ')
        return v
    
    @validator('first_name', 'last_name')
    def validate_name(cls, v):
        """Проверка формата имени"""
        if v is None:
            return v
        
        v = v.strip()
        if not v:
            return None
        
        # Разрешаем буквы, пробелы и дефисы (для двойных фамилий или имён с дефисом)
        if not re.match(r'^[A-Za-z\s\-]+$', v):
            raise ValueError('Имя может содержать только буквы, пробелы и дефисы')
        
        # Проверка длины
        if len(v) > 50:
            raise ValueError('Длина имени не должна превышать 50 символов')
        
        return v
    
    @validator('email')
    def validate_email_domain(cls, v):
        """Опционально: проверка домена электронной почты"""
        # Здесь можно добавить чёрный или белый список доменов
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для операций с базой данных"""
        return {
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'password': self.password  # Примечание: пароль должен быть хеширован
        }

class UserUpdate(BaseModel):
    """Схема для обновления пользователя"""
    first_name: Optional[str] = Field(None, max_length=50, description="Имя")
    last_name: Optional[str] = Field(None, max_length=50, description="Фамилия")
    phone: Optional[str] = Field(None, max_length=20, description="Номер телефона")
    avatar_url: Optional[str] = Field(None, max_length=500, description="URL аватара")
    
    @validator('first_name', 'last_name')
    def validate_name(cls, v):
        """Проверка формата имени"""
        if v and not v.replace(' ', '').replace('-', '').isalpha():
            raise ValueError('Имя может содержать только буквы, пробелы и дефисы')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        """Проверка формата номера телефона"""
        if v:
            # Удаляем все нецифровые символы (кроме знака +)
            cleaned = v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if not cleaned.startswith('+'):
                # Если не международный формат, проверяем, что это цифры
                if not cleaned.isdigit():
                    raise ValueError('Неверный формат номера телефона')
            else:
                # Международный номер: после + должны быть цифры
                if not cleaned[1:].isdigit():
                    raise ValueError('Неверный формат международного номера телефона')
        return v

class UserResponse(UserBase):
    """Схема ответа с данными пользователя"""
    id: int
    is_verified: bool
    is_active: bool
    is_profile_completed: bool
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    
    @property
    def display_name(self) -> str:
        """Получает отображаемое имя"""
        if self.full_name:
            return self.full_name
        return self.email.split('@')[0]  # Используем часть email до @ как запасной вариант
    
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    """Токен аутентификации"""
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None

class TokenData(BaseModel):
    """Данные токена"""
    email: Optional[str] = None
    user_id: Optional[int] = None

class UserProfile(BaseModel):
    """Схема профиля пользователя"""
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: Optional[str]
    phone: Optional[str]
    avatar_url: Optional[str]
    is_verified: bool
    is_profile_completed: bool
    
    @classmethod
    def from_user(cls, user):
        """Создание UserProfile из объекта User"""
        return cls(
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            phone=user.phone,
            avatar_url=user.avatar_url,
            is_verified=user.is_verified,
            is_profile_completed=user.is_profile_completed
        )