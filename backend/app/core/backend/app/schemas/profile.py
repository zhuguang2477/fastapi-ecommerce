# backend/app/schemas/profile.py
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class ProfileUpdate(BaseModel):
    """Обновление профиля"""
    first_name: Optional[str] = Field(None, max_length=50, description="Имя")
    last_name: Optional[str] = Field(None, max_length=50, description="Фамилия")
    phone: Optional[str] = Field(None, max_length=20, description="Номер телефона")
    avatar_url: Optional[str] = Field(None, max_length=500, description="URL аватара")
    
    @validator('first_name', 'last_name')
    def validate_name(cls, v):
        """Проверка формата имени"""
        if v and not v.replace(' ', '').isalpha():
            raise ValueError('Имя может содержать только буквы и пробелы')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        """Проверка формата номера телефона"""
        if v and not v.replace('+', '').replace(' ', '').replace('-', '').isdigit():
            raise ValueError('Неверный формат номера телефона')
        return v

class ProfileResponse(BaseModel):
    """Ответ с данными профиля"""
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    is_verified: bool
    is_profile_completed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True