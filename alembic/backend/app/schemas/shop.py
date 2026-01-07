# backend/app/schemas/shop.py
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from typing import Optional, Dict, Any
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
    
    model_config = ConfigDict(
        from_attributes=True
    )


class ShopUpdate(BaseModel):
    """Обновление информации о магазине"""
    name: Optional[str] = None
    description: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    timezone: Optional[str] = None
    
    @field_validator('contact_phone')
    def validate_phone(cls, v):
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
            raise ValueError('Некорректный формат телефона')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Обновленный магазин",
                "description": "Новое описание магазина",
                "contact_email": "contact@example.com",
                "contact_phone": "+7 (999) 123-45-67",
                "address": "ул. Примерная, 123",
                "website": "https://example.com",
                "timezone": "Europe/Moscow"
            }
        }
    )


class ShopAdminSettings(BaseModel):
    """Административные настройки магазина"""
    join_password: Optional[str] = None
    require_approval: Optional[bool] = True
    max_members: Optional[int] = 50
    default_member_role: Optional[str] = "viewer"
    allow_guest_orders: Optional[bool] = True
    order_confirmation_required: Optional[bool] = False
    auto_approve_orders: Optional[bool] = False
    
    @field_validator('max_members')
    def validate_max_members(cls, v):
        if v is not None and v < 1:
            raise ValueError('Максимальное количество участников должно быть не менее 1')
        return v
    
    @field_validator('default_member_role')
    def validate_role(cls, v):
        valid_roles = ["viewer", "editor", "admin"]
        if v is not None and v not in valid_roles:
            raise ValueError(f'Роль должна быть одной из: {", ".join(valid_roles)}')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "join_password": "новый_пароль",
                "require_approval": True,
                "max_members": 20,
                "default_member_role": "editor",
                "allow_guest_orders": True,
                "order_confirmation_required": True,
                "auto_approve_orders": False
            }
        }
    )


class ShopBasicInfo(BaseModel):
    """Основная информация о магазине (публичная)"""
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True
    )


class ShopStats(BaseModel):
    """Статистика магазина"""
    total_products: int = 0
    total_orders: int = 0
    total_customers: int = 0
    total_revenue: float = 0.0
    active_members: int = 0
    
    model_config = ConfigDict(
        from_attributes=True
    )