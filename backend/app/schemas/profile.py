# backend/app/schemas/profile.py
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class ProfileUpdate(BaseModel):
    """Обновление личных данных"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "first_name": "Иван",
                "last_name": "Иванов",
                "phone": "+79991234567"
            }
        }
    )


class ProfileResponse(BaseModel):
    """Ответы на личные данные"""
    id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    is_profile_completed: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "user@example.com",
                "first_name": "Иван",
                "last_name": "Иванов",
                "phone": "+79991234567",
                "is_profile_completed": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }
    )