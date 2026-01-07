# backend/app/schemas/auth.py
"""
Модели аутентификации
"""
from pydantic import BaseModel, EmailStr, Field, validator
import re


class SendOTPRequest(BaseModel):
    """Запрос на отправку OTP"""
    email: EmailStr = Field(..., description="Электронная почта пользователя")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class ConfirmOTPRequest(BaseModel):
    """Запрос подтверждения OTP"""
    email: EmailStr = Field(..., description="Электронная почта пользователя")
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-значный код подтверждения")
    
    @validator('otp_code')
    def validate_otp_code(cls, v):
        if not v.isdigit():
            raise ValueError('Код подтверждения должен состоять из 6 цифр')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "otp_code": "123456"
            }
        }


class CompleteProfileRequest(BaseModel):
    """Запрос на заполнение профиля"""
    first_name: str = Field(..., min_length=1, max_length=50, description="Имя")
    last_name: str = Field(..., min_length=1, max_length=50, description="Фамилия")
    phone: str = Field(..., description="Номер телефона")
    
    @validator('phone')
    def validate_phone(cls, v):
        # Базовая проверка номера телефона
        phone_pattern = re.compile(r'^\+?[1-9]\d{1,14}$')
        if not phone_pattern.match(v):
            raise ValueError('Неверный формат номера телефона. Используйте международный формат.')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "Иван",
                "last_name": "Иванов",
                "phone": "+79161234567"
            }
        }


class LoginRequest(BaseModel):
    """Запрос на вход (устарело, используется для совместимости)"""
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }


class RegisterRequest(BaseModel):
    """Запрос на регистрацию (традиционный способ)"""
    email: EmailStr = Field(..., description="Электронная почта пользователя")
    password: str = Field(..., min_length=6, max_length=100, description="Пароль")
    first_name: str = Field(..., min_length=1, max_length=50, description="Имя")
    last_name: str = Field(..., min_length=1, max_length=50, description="Фамилия")
    phone: str = Field(..., description="Номер телефона")
    
    @validator('phone')
    def validate_phone(cls, v):
        # Базовая проверка номера телефона
        phone_pattern = re.compile(r'^\+?[1-9]\d{1,14}$')
        if not phone_pattern.match(v):
            raise ValueError('Неверный формат номера телефона. Используйте международный формат.')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        # Проверка сложности пароля (опционально)
        if len(v) < 6:
            raise ValueError('Пароль должен содержать не менее 6 символов')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "first_name": "Иван",
                "last_name": "Иванов",
                "phone": "+79161234567"
            }
        }