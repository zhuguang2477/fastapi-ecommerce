# backend/app/schemas/user.py
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Базовая модель пользователя"""
    email: EmailStr


class UserCreate(UserBase):
    """Пользователи создают модели (для регистрации OTP)"""
    full_name: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "full_name": "John Doe"
            }
        }
    )


class UserResponse(UserBase):
    """Модель отклика пользователя"""
    id: int
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "user@example.com",
                "full_name": "John Doe",
                "phone": "+1234567890",
                "is_verified": True,
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "last_login": "2024-01-15T10:30:00Z"
            }
        }
    )


class UserUpdate(BaseModel):
    """Модель обновления пользователя"""
    full_name: Optional[str] = None
    phone: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "Jane Doe",
                "phone": "+1234567890"
            }
        }
    )


class Token(BaseModel):
    """Модель токена JWT"""
    access_token: str
    token_type: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer"
            }
        }
    )


class TokenData(BaseModel):
    """Модель токенов"""
    email: Optional[str] = None
    user_id: Optional[int] = None