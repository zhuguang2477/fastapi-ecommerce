# backend/app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field, validator, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
import re

class UserBase(BaseModel):
    """Базовая информация о пользователе"""
    email: EmailStr = Field(..., description="Электронная почта пользователя")
    first_name: Optional[str] = Field(None, max_length=50, description="Имя")
    last_name: Optional[str] = Field(None, max_length=50, description="Фамилия")
    phone: Optional[str] = Field(None, max_length=20, description="Номер телефона")
    
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


# ИЗМЕНЕНО: Восстановить класс UserCreate (без пароля) вместо UserCreateWithoutPassword
class UserCreate(UserBase):
    """Схема для создания пользователя (без пароля)"""
    
    @validator('first_name', 'last_name')
    def validate_name(cls, v):
        """Проверка формата имени"""
        if v is None:
            return v
        
        v = v.strip()
        if not v:
            return None
        
        # Разрешаем буквы, пробелы и дефисы (для двойных фамилий или имён с дефисом)
        if not re.match(r'^[A-Za-zА-Яа-яЁё\s\-]+$', v):
            raise ValueError('Имя может содержать только буквы, пробелы и дефисы')
        
        # Проверка длины
        if len(v) > 50:
            raise ValueError('Длина имени не должна превышать 50 символов')
        
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
            
            # Проверка длины
            if len(cleaned) < 10 or len(cleaned) > 15:
                raise ValueError('Номер телефона должен содержать от 10 до 15 цифр')
        return v
    
    @validator('email')
    def validate_email_domain(cls, v):
        """Проверка домена электронной почты"""
        # Пример: запрещаем временные email-сервисы
        temp_domains = ['tempmail.com', 'throwawaymail.com', '10minutemail.com']
        domain = v.split('@')[1].lower()
        if domain in temp_domains:
            raise ValueError('Использование временных email-адресов запрещено')
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для операций с базой данных"""
        return {
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone
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
        if v and not re.match(r'^[A-Za-zА-Яа-яЁё\s\-]+$', v.replace(' ', '')):
            raise ValueError('Имя может содержать только буквы, пробелы и дефисы')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        """Проверка формата номера телефона"""
        if v:
            cleaned = v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if not cleaned.startswith('+'):
                if not cleaned.isdigit():
                    raise ValueError('Неверный формат номера телефона')
            else:
                if not cleaned[1:].isdigit():
                    raise ValueError('Неверный формат международного номера телефона')
        return v


# ИЗМЕНЕНО: Добавлены поля OTP-верификации
class UserResponse(UserBase):
    """Схема ответа с данными пользователя"""
    id: int
    is_verified: bool = Field(False, description="Почта верифицирована через OTP")
    is_active: bool = Field(True, description="Активен ли пользователь")
    is_profile_completed: bool = Field(False, description="Профиль полностью заполнен")
    avatar_url: Optional[str] = None
    otp_enabled: bool = Field(False, description="Включена ли двухфакторная аутентификация")
    otp_verified: bool = Field(False, description="Пройдена ли первичная OTP верификация")
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    @property
    def display_name(self) -> str:
        """Получает отображаемое имя"""
        if self.full_name:
            return self.full_name
        return self.email.split('@')[0] 
    
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Токен аутентификации"""
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None


# ИЗМЕНЕНО: Добавлено поле is_verified
class TokenData(BaseModel):
    """Данные токена"""
    email: Optional[str] = None
    user_id: Optional[int] = None
    is_verified: Optional[bool] = None


# ИЗМЕНЕНО: Добавлены поля OTP
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
    otp_enabled: bool
    otp_verified: bool
    
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
            is_profile_completed=user.is_profile_completed,
            otp_enabled=user.otp_enabled,
            otp_verified=user.otp_verified
        )


# ДОБАВЛЕНО: Новый класс для статуса OTP-верификации
class OTPVerificationStatus(BaseModel):
    """Статус OTP верификации пользователя"""
    email: str
    is_verified: bool
    otp_enabled: bool
    otp_verified: bool
    verification_expires_at: Optional[datetime] = None
    last_otp_sent_at: Optional[datetime] = None


# ДОБАВЛЕНО: Класс пользователя с полной информацией о статусе OTP
class UserWithOTPStatus(UserResponse):
    """Пользователь с полной информацией о статусе OTP"""
    otp_status: OTPVerificationStatus