# backend/app/schemas/order.py
from typing import Literal
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    """Перечисление статусов заказа"""
    PENDING = "pending"  # Ожидает обработки
    PAID = "paid"  # Оплачен
    PROCESSING = "processing"  # Обрабатывается
    SHIPPED = "shipped"  # Отправлен
    DELIVERED = "delivered"  # Доставлен
    CANCELLED = "cancelled"  # Отменен
    REFUNDED = "refunded"  # Возвращен

class PaymentStatus(str, Enum):
    """Перечисление статусов оплаты"""
    UNPAID = "unpaid"  # Не оплачен
    PAID = "paid"  # Оплачен
    FAILED = "failed"  # Ошибка оплаты
    REFUNDED = "refunded"  # Возвращен

class PaymentMethod(str, Enum):
    """Перечисление способов оплаты"""
    CREDIT_CARD = "credit_card"
    ALIPAY = "alipay"
    WECHAT_PAY = "wechat_pay"
    CASH_ON_DELIVERY = "cash_on_delivery"

# Информация об адресе
class Address(BaseModel):
    """Информация об адресе"""
    name: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str = "China"

# Позиция товара в заказе
class OrderItemBase(BaseModel):
    product_id: int
    product_name: str
    unit_price: float = Field(gt=0, description="Цена за единицу должна быть больше 0")
    quantity: int = Field(gt=0, description="Количество должно быть больше 0")
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Количество должно быть больше 0')
        return v

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemInDB(OrderItemBase):
    id: int
    order_id: int
    total_price: float
    created_at: datetime
    
    class Config:
        from_attributes = True

# Информация о заказе
class OrderBase(BaseModel):
    customer_email: str
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    shipping_address: Optional[Dict[str, Any]] = None
    billing_address: Optional[Dict[str, Any]] = None
    customer_notes: Optional[str] = None
    payment_method: Optional[PaymentMethod] = None

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    admin_notes: Optional[str] = None
    tracking_number: Optional[str] = None
    shipping_amount: Optional[float] = None

class OrderInDB(OrderBase):
    id: int
    shop_id: int
    order_number: str
    total_amount: float
    subtotal: float
    tax_amount: float
    shipping_amount: float
    discount_amount: float
    status: OrderStatus
    payment_status: PaymentStatus
    payment_method: Optional[str] = None
    admin_notes: Optional[str] = None
    tracking_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    paid_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    items: List[OrderItemInDB] = []
    
    class Config:
        from_attributes = True

class OrderList(BaseModel):
    """Ответ со списком заказов"""
    orders: List[OrderInDB]
    total: int
    page: int
    page_size: int
    total_pages: int

# Статистика по заказам
class OrderStats(BaseModel):
    total_orders: int
    total_revenue: float
    average_order_value: float
    pending_orders: int
    paid_orders: int
    delivered_orders: int
    cancelled_orders: int
    
class DailyOrderStats(BaseModel):
    date: str
    orders_count: int
    total_revenue: float

# Добавить следующее содержимое в backend/app/schemas/order.py

class OrderFilter(BaseModel):
    """Условия фильтрации заказов"""
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    payment_method: Optional[PaymentMethod] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    order_number: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    has_customer_notes: Optional[bool] = None
    
    class Config:
        from_attributes = True


class OrderSearch(BaseModel):
    """Условия поиска заказов"""
    query: Optional[str] = None
    filter: Optional[OrderFilter] = None
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = "desc"
    
    class Config:
        from_attributes = True


class OrderBulkUpdate(BaseModel):
    """Массовое обновление заказов"""
    order_ids: List[int]
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    admin_notes: Optional[str] = None
    tracking_number: Optional[str] = None
    shipping_method: Optional[str] = None
    shipping_carrier: Optional[str] = None
    shipping_amount: Optional[float] = None
    discount_amount: Optional[float] = None
    
    @validator('order_ids')
    def validate_order_ids(cls, v):
        if not v:
            raise ValueError('Список ID заказов не может быть пустым')
        if len(v) > 100:
            raise ValueError('Можно массово обновить не более 100 заказов за раз')
        return v


class OrderStatusUpdate(BaseModel):
    """Обновление статуса заказа"""
    status: OrderStatus
    notes: Optional[str] = None
    send_notification: bool = True
    
    @validator('notes')
    def validate_notes(cls, v):
        if v and len(v) > 500:
            raise ValueError('Примечание не может превышать 500 символов')
        return v


class OrderExportRequest(BaseModel):
    """Запрос на экспорт заказов"""
    format: Literal["csv", "excel", "json"] = "csv"
    columns: List[str] = Field(default_factory=lambda: [
        "order_number", "customer_email", "customer_name", 
        "total_amount", "status", "payment_status", "created_at"
    ])
    filter: Optional[OrderFilter] = None
    
    @validator('columns')
    def validate_columns(cls, v):
        allowed_columns = [
            "id", "order_number", "shop_id", "customer_id", "customer_email",
            "customer_name", "customer_phone", "total_amount", "subtotal",
            "tax_amount", "shipping_amount", "discount_amount", "status",
            "payment_status", "payment_method", "shipping_address", 
            "billing_address", "customer_notes", "admin_notes", 
            "tracking_number", "created_at", "updated_at", "paid_at", 
            "shipped_at", "item_count"
        ]
        for col in v:
            if col not in allowed_columns:
                raise ValueError(f'Недопустимый столбец: {col}')
        return v