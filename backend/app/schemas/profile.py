# backend/app/schemas/profile.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class ProfileUpdate(BaseModel):
    """Схема для обновления профиля"""
    first_name: Optional[str] = Field(None, max_length=50, description="Имя")
    last_name: Optional[str] = Field(None, max_length=50, description="Фамилия")
    phone: Optional[str] = Field(None, max_length=20, description="Номер телефона")
    avatar_url: Optional[str] = Field(None, max_length=500, description="URL аватара")

class CompleteProfileRequest(BaseModel):
    """Схема для завершения регистрации профиля"""
    first_name: str = Field(..., min_length=1, max_length=50, description="Имя")
    last_name: str = Field(..., min_length=1, max_length=50, description="Фамилия")
    phone: str = Field(..., min_length=10, max_length=20, description="Номер телефона")

class ProfileResponse(BaseModel):
    """Схема ответа с профилем пользователя"""
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: Optional[str]
    phone: Optional[str]
    avatar_url: Optional[str]
    is_verified: bool
    is_profile_completed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None