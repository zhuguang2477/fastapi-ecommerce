# backend/app/schemas/customer.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class CustomerStatus(str, Enum):
    """Перечисление статусов клиентов"""
    ACTIVE = "active"  
    INACTIVE = "inactive"

class CustomerType(str, Enum):
    """Перечисление типов клиентов"""
    NEW = "new"      
    REGULAR = "regular" 
    VIP = "vip"        

class CustomerBase(BaseModel):
    """Базовая информация о клиенте"""
    email: str = Field(..., description="Электронная почта клиента")
    name: Optional[str] = Field(None, description="Имя клиента")
    phone: Optional[str] = Field(None, description="Телефон клиента")

class CustomerResponse(CustomerBase):
    """Ответ с данными клиента"""
    id: int = Field(..., description="ID клиента")
    order_count: int = Field(0, description="Общее количество заказов")
    total_spent: float = Field(0.0, description="Общая сумма расходов")
    avg_order_value: float = Field(0.0, description="Средняя стоимость заказа")
    first_order_date: Optional[datetime] = Field(None, description="Дата первого заказа")
    last_order_date: Optional[datetime] = Field(None, description="Дата последнего заказа")
    status: CustomerStatus = Field(CustomerStatus.ACTIVE, description="Статус клиента")
    type: CustomerType = Field(CustomerType.NEW, description="Тип клиента")
    order_statuses: List[str] = Field(default_factory=list, description="Список статусов заказов")
    order_numbers: List[str] = Field(default_factory=list, description="Список номеров заказов")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")
    
    class Config:
        from_attributes = True

class CustomerDetail(CustomerResponse):
    """Подробная информация о клиенте"""
    recent_orders: List[Dict[str, Any]] = Field(default_factory=list, description="Последние заказы")

class CustomerList(BaseModel):
    """Ответ со списком клиентов"""
    customers: List[CustomerResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class CustomerStats(BaseModel):
    """Статистика по клиентам"""
    total_customers: int
    active_customers: int
    inactive_customers: int
    new_customers_30d: int
    avg_order_value: float
    total_revenue: float
    avg_lifetime_value: float
    max_lifetime_value: float
    min_lifetime_value: float

class CustomerFilter(BaseModel):
    """Условия фильтрации клиентов"""
    email: Optional[str] = None
    name: Optional[str] = None
    status: Optional[CustomerStatus] = None
    customer_type: Optional[CustomerType] = None
    min_orders: Optional[int] = None
    max_orders: Optional[int] = None
    min_spent: Optional[float] = None
    max_spent: Optional[float] = None
    
    class Config:
        from_attributes = True

class CustomerSearch(BaseModel):
    """Условия поиска клиентов"""
    query: Optional[str] = None
    filter: Optional[CustomerFilter] = None
    sort_by: Optional[str] = "last_order_date"
    sort_order: Optional[str] = "desc"
    
    class Config:
        from_attributes = True