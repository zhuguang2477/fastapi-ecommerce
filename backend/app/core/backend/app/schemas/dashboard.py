# backend/app/schemas/dashboard.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class CategoryStat(BaseModel):
    """Статистика по категориям"""
    name: str
    count: int


class WeeklyActivity(BaseModel):
    """Данные еженедельной активности"""
    week: str  # Дата начала недели, формат: YYYY-MM-DD
    orders: int
    customers: int


class MonthlyRevenue(BaseModel):
    """Ежемесячная выручка"""
    month: str  # Месяц, формат: YYYY-MM
    revenue: float
    order_count: Optional[int] = 0


class UserActivity(BaseModel):
    """Активность пользователей"""
    week: List[str]
    visits: List[int]  # Можно использовать количество заказов или посещений


class DashboardStats(BaseModel):
    """Статистика панели управления"""
    popular_categories: List[CategoryStat]
    user_activity: UserActivity
    average_product_rating: float
    average_order_value: float
    monthly_revenue: List[MonthlyRevenue]
    
    class Config:
        from_attributes = True


class QuickStats(BaseModel):
    """Быстрая статистика"""
    today_orders: int
    today_revenue: float
    total_products: int
    total_customers: int
    out_of_stock: int
    pending_orders: int
    conversion_rate: Optional[float] = None