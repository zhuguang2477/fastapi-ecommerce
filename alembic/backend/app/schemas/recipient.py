# backend/app/schemas/recipient.py
"""
Pydantic-схемы для получателей
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class RecipientBase(BaseModel):
    """Базовая схема получателя"""
    recipient_name: str = Field(..., min_length=1, max_length=100, description="Имя получателя")
    recipient_phone: str = Field(..., min_length=1, max_length=50, description="Телефон получателя")
    recipient_email: Optional[str] = Field(None, max_length=255, description="Email получателя")
    
    country: str = Field(default="Россия", max_length=100, description="Страна")
    province: str = Field(..., max_length=100, description="Область/край/республика")
    city: str = Field(..., max_length=100, description="Город")
    district: Optional[str] = Field(None, max_length=100, description="Район")
    address_line1: str = Field(..., max_length=500, description="Адрес (строка 1)")
    address_line2: Optional[str] = Field(None, max_length=500, description="Адрес (строка 2)")
    postal_code: Optional[str] = Field(None, max_length=20, description="Почтовый индекс")
    
    address_label: Optional[str] = Field(None, max_length=100, description="Метка адреса")
    address_type: str = Field(default="shipping", description="Тип адреса: shipping, billing, both")
    
    is_default_shipping: bool = Field(default=False, description="Адрес доставки по умолчанию")
    is_default_billing: bool = Field(default=False, description="Платежный адрес по умолчанию")
    
    latitude: Optional[str] = Field(None, max_length=50, description="Широта")
    longitude: Optional[str] = Field(None, max_length=50, description="Долгота")
    
    notes: Optional[str] = Field(None, description="Примечания")
    
    @validator('recipient_phone')
    def validate_phone(cls, v):
        # Базовая проверка номера телефона
        if not v.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '').isdigit():
            raise ValueError('Неправильный формат номера телефона')
        return v
    
    @validator('recipient_email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Неправильный формат email')
        return v
    
    @validator('address_type')
    def validate_address_type(cls, v):
        allowed_types = ['shipping', 'billing', 'both']
        if v not in allowed_types:
            raise ValueError(f'Тип адреса должен быть одним из: {", ".join(allowed_types)}')
        return v


class RecipientCreate(RecipientBase):
    """Схема создания получателя"""
    shop_id: int = Field(..., description="ID магазина")
    customer_id: Optional[int] = Field(None, description="ID клиента")
    created_by: Optional[int] = Field(None, description="ID пользователя, создавшего запись")


class RecipientUpdate(BaseModel):
    """Схема обновления получателя"""
    recipient_name: Optional[str] = Field(None, min_length=1, max_length=100)
    recipient_phone: Optional[str] = Field(None, min_length=1, max_length=50)
    recipient_email: Optional[str] = Field(None, max_length=255)
    
    country: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    address_line1: Optional[str] = Field(None, max_length=500)
    address_line2: Optional[str] = Field(None, max_length=500)
    postal_code: Optional[str] = Field(None, max_length=20)
    
    address_label: Optional[str] = Field(None, max_length=100)
    address_type: Optional[str] = Field(None, description="Тип адреса: shipping, billing, both")
    
    is_default_shipping: Optional[bool] = Field(None)
    is_default_billing: Optional[bool] = Field(None)
    
    latitude: Optional[str] = Field(None, max_length=50)
    longitude: Optional[str] = Field(None, max_length=50)
    
    is_active: Optional[bool] = Field(None)
    notes: Optional[str] = Field(None)
    
    @validator('address_type')
    def validate_address_type(cls, v):
        if v and v not in ['shipping', 'billing', 'both']:
            raise ValueError('Тип адреса должен быть одним из: shipping, billing или both')
        return v


class RecipientInDB(RecipientBase):
    """Схема получателя в базе данных"""
    id: int = Field(..., description="ID получателя")
    shop_id: int = Field(..., description="ID магазина")
    customer_id: int = Field(..., description="ID клиента")
    is_active: bool = Field(default=True, description="Активен ли адрес")
    is_verified: bool = Field(default=False, description="Проверен ли адрес")
    verification_date: Optional[datetime] = Field(None, description="Дата проверки")
    created_by: Optional[int] = Field(None, description="ID пользователя, создавшего запись")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")
    
    class Config:
        from_attributes = True


class RecipientResponse(RecipientInDB):
    """Схема ответа для получателя"""
    full_address: str = Field(..., description="Полный адрес")
    short_address: str = Field(..., description="Краткий адрес")
    is_default_address: bool = Field(..., description="Является ли адресом по умолчанию")


class RecipientList(BaseModel):
    """Схема ответа для списка получателей"""
    recipients: List[RecipientResponse] = Field(..., description="Список получателей")
    total: int = Field(..., description="Общее количество")
    page: int = Field(..., description="Текущая страница")
    page_size: int = Field(..., description="Размер страницы")
    total_pages: int = Field(..., description="Общее количество страниц")