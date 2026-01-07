# backend/app/schemas/basket.py
"""
Pydantic-схемы для корзины покупок
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class BasketStatus(str, Enum):
    """Перечисление статусов корзины"""
    ACTIVE = "active"
    ABANDONED = "abandoned"
    CONVERTED = "converted"
    EXPIRED = "expired"


class BasketBase(BaseModel):
    """Базовая схема корзины"""
    basket_token: str = Field(..., max_length=100, description="Уникальный токен корзины")
    session_id: Optional[str] = Field(None, max_length=100, description="Идентификатор сессии")
    status: BasketStatus = Field(default=BasketStatus.ACTIVE, description="Статус корзины")
    is_guest: bool = Field(default=False, description="Гостевая ли корзина")
    
    currency: str = Field(default="CNY", max_length=10, description="Валюта")
    coupon_code: Optional[str] = Field(None, max_length=100, description="Код купона")
    discount_rules: Optional[Dict[str, Any]] = Field(None, description="Правила скидок")
    
    shipping_method: Optional[str] = Field(None, max_length=100, description="Способ доставки")
    shipping_address_id: Optional[int] = Field(None, description="ID адреса доставки")
    
    expires_at: Optional[datetime] = Field(None, description="Время истечения срока")
    basket_metadata: Optional[Dict[str, Any]] = Field(None, description="Метаданные")
    notes: Optional[str] = Field(None, description="Примечания")


class BasketCreate(BasketBase):
    """Схема создания корзины"""
    shop_id: int = Field(..., description="ID магазина")
    customer_id: Optional[int] = Field(None, description="ID клиента")


class BasketUpdate(BaseModel):
    """Схема обновления корзины"""
    status: Optional[BasketStatus] = Field(None)
    currency: Optional[str] = Field(None, max_length=10)
    coupon_code: Optional[str] = Field(None, max_length=100)
    discount_rules: Optional[Dict[str, Any]] = Field(None)
    
    shipping_method: Optional[str] = Field(None, max_length=100)
    shipping_address_id: Optional[int] = Field(None)
    
    expires_at: Optional[datetime] = Field(None)
    basket_metadata: Optional[Dict[str, Any]] = Field(None)
    notes: Optional[str] = Field(None)


class BasketItemBase(BaseModel):
    """Базовая схема товара в корзине"""
    product_id: int = Field(..., description="ID товара")
    variant_id: Optional[int] = Field(None, description="ID варианта товара")
    quantity: int = Field(default=1, ge=1, description="Количество")
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v < 1:
            raise ValueError('Количество должно быть больше 0')
        return v


class BasketItemCreate(BasketItemBase):
    """Схема создания товара в корзине"""
    basket_id: int = Field(..., description="ID корзины")


class BasketItemUpdate(BaseModel):
    """Схема обновления товара в корзине"""
    quantity: Optional[int] = Field(None, ge=1)
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v is not None and v < 1:
            raise ValueError('Количество должно быть больше 0')
        return v


class BasketItemResponse(BasketItemBase):
    """Схема ответа для товара в корзине"""
    id: int = Field(..., description="ID товара в корзине")
    basket_id: int = Field(..., description="ID корзины")
    product_name: str = Field(..., description="Название товара")
    product_sku: Optional[str] = Field(None, description="Артикул товара")
    variant_name: Optional[str] = Field(None, description="Название варианта")
    variant_attributes: Optional[Dict[str, Any]] = Field(None, description="Атрибуты варианта")
    unit_price: float = Field(..., description="Цена за единицу")
    original_price: Optional[float] = Field(None, description="Оригинальная цена")
    discount_amount: float = Field(0.0, description="Сумма скидки")
    max_quantity: Optional[int] = Field(None, description="Максимальное количество")
    product_image_url: Optional[str] = Field(None, description="URL изображения товара")
    product_slug: Optional[str] = Field(None, description="Slug товара")
    is_in_stock: bool = Field(..., description="В наличии")
    stock_quantity: Optional[int] = Field(None, description="Количество на складе")
    requires_shipping: bool = Field(..., description="Требует доставки")
    weight: Optional[float] = Field(None, description="Вес")
    dimensions: Optional[Dict[str, Any]] = Field(None, description="Размеры")
    discount_percentage: float = Field(0.0, description="Процент скидки")
    discount_reason: Optional[str] = Field(None, description="Причина скидки")
    added_at: datetime = Field(..., description="Дата добавления")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")
    item_metadata: Optional[Dict[str, Any]] = Field(None, description="Метаданные товара")
    notes: Optional[str] = Field(None, description="Примечания")
    
    line_total: float = Field(..., description="Общая стоимость строки")
    formatted_unit_price: str = Field(..., description="Отформатированная цена за единицу")
    formatted_line_total: str = Field(..., description="Отформатированная общая стоимость")
    discount_percentage_display: float = Field(..., description="Отображаемый процент скидки")
    display_name: str = Field(..., description="Отображаемое название")
    is_discounted: bool = Field(..., description="Есть ли скидка")
    can_increase_quantity: bool = Field(..., description="Можно ли увеличить количество")
    
    class Config:
        from_attributes = True


class BasketResponse(BasketBase):
    """Схема ответа для корзины"""
    id: int = Field(..., description="ID корзины")
    shop_id: int = Field(..., description="ID магазина")
    customer_id: Optional[int] = Field(None, description="ID клиента")
    subtotal: float = Field(0.0, description="Промежуточная сумма")
    discount_amount: float = Field(0.0, description="Сумма скидки")
    shipping_amount: float = Field(0.0, description="Стоимость доставки")
    tax_amount: float = Field(0.0, description="Сумма налога")
    total_amount: float = Field(0.0, description="Общая сумма")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")
    last_activity_at: datetime = Field(..., description="Последняя активность")
    
    item_count: int = Field(0, description="Количество товаров")
    unique_item_count: int = Field(0, description="Количество уникальных товаров")
    is_empty: bool = Field(..., description="Пустая ли корзина")
    is_expired: bool = Field(..., description="Истекла ли корзина")
    formatted_total: str = Field(..., description="Отформатированная общая сумма")
    
    items: Optional[List[BasketItemResponse]] = Field(None, description="Товары в корзине")
    
    class Config:
        from_attributes = True


class BasketList(BaseModel):
    """Схема ответа списка корзин"""
    baskets: List[BasketResponse] = Field(..., description="Список корзин")
    total: int = Field(..., description="Общее количество")
    page: int = Field(..., description="Текущая страница")
    page_size: int = Field(..., description="Размер страницы")
    total_pages: int = Field(..., description="Общее количество страниц")