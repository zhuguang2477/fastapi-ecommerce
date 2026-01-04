# backend/app/schemas/shop_settings.py
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, Dict, Any, List
from datetime import datetime

class ShopSettingsBase(BaseModel):
    """Базовая информация о настройках магазина"""
    official_name: Optional[str] = Field(None, max_length=200, description="Официальное название")
    contact_email: Optional[EmailStr] = Field(None, description="Контактный email")
    phone: Optional[str] = Field(None, max_length=20, description="Контактный телефон")
    address: Optional[str] = Field(None, description="Адрес")
    currency: Optional[str] = Field("CNY", max_length=3, description="Код валюты")
    timezone: Optional[str] = Field("Asia/Shanghai", description="Часовой пояс")
    language: Optional[str] = Field("zh_CN", description="Код языка")
    meta_title: Optional[str] = Field(None, max_length=200, description="Meta-заголовок")
    meta_description: Optional[str] = Field(None, description="Meta-описание")
    meta_keywords: Optional[str] = Field(None, description="Meta-ключевые слова")
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.replace('+', '').replace(' ', '').replace('-', '').isdigit():
            raise ValueError('Неправильный формат номера телефона')
        return v
    
    @validator('currency')
    def validate_currency(cls, v):
        if v and len(v) != 3:
            raise ValueError('Код валюты должен состоять из 3 символов')
        return v.upper() if v else v

class SocialLinks(BaseModel):
    """Ссылки на социальные сети"""
    facebook: Optional[str] = None
    twitter: Optional[str] = None
    instagram: Optional[str] = None
    linkedin: Optional[str] = None
    youtube: Optional[str] = None
    wechat: Optional[str] = None
    weibo: Optional[str] = None

class ShopSettingsCreate(ShopSettingsBase):
    """Создание настроек магазина"""
    shop_id: int = Field(..., description="ID магазина")
    social_links: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Ссылки на социальные сети")

class ShopSettingsUpdate(BaseModel):
    """Обновление настроек магазина"""
    official_name: Optional[str] = Field(None, max_length=200)
    contact_email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    currency: Optional[str] = Field(None, max_length=3)
    timezone: Optional[str] = None
    language: Optional[str] = None
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    social_links: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None 

class ShopSettingsResponse(ShopSettingsBase):
    """Ответ с настройками магазина"""
    id: int = Field(..., description="ID настроек")
    shop_id: int = Field(..., description="ID магазина")
    social_links: Dict[str, Any] = Field(default_factory=dict, description="Ссылки на социальные сети")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Пользовательские настройки")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")
    
    class Config:
        from_attributes = True