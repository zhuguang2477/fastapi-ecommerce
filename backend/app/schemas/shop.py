# backend/app/schemas/shop.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class ShopCreate(BaseModel):
    """Создать магазин"""
    name: str
    description: Optional[str] = None
    join_password: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Мой магазин",
                "description": "Описание моего магазина",
                "join_password": "пароль123"
            }
        }
    )


class ShopJoinRequest(BaseModel):
    """Присоединяйтесь к запросу магазина"""
    join_password: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "join_password": "пароль123"
            }
        }
    )


class ShopResponse(BaseModel):
    """Магазин Ответить"""
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True
    )


class ShopMemberResponse(BaseModel):
    """Ответить Участники магазина"""
    id: int
    shop_id: int
    user_id: int
    user_email: str
    user_full_name: str
    role: str
    is_approved: bool
    created_at: datetime