# backend/app/models/analytics.py
"""
分析数据模型
用于存储聚合分析数据
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, Numeric, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.database import Base


class AnalyticsReport(Base):
    """Модель аналитического отчета"""
    __tablename__ = "analytics_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    
    # Информация об отчете
    report_type = Column(String(50), nullable=False, index=True)
    report_name = Column(String(200), nullable=True)
    period_type = Column(String(20), nullable=False)
    
    # Временной диапазон
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Данные отчета (в формате JSON)
    report_data = Column(JSON, nullable=False, default=dict)
    
    # Метаданные
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    generation_time = Column(DateTime(timezone=True), server_default=func.now())
    
    # Статус
    is_ready = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    
    # Связи
    shop = relationship("Shop")
    generator = relationship("User")
    
    # Индексы
    __table_args__ = (
        Index('ix_analytics_shop_type_period', 'shop_id', 'report_type', 'period_start'),
    )
    
    def __repr__(self):
        return f"<AnalyticsReport(id={self.id}, shop_id={self.shop_id}, report_type='{self.report_type}')>"
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь"""
        return {
            'id': self.id,
            'shop_id': self.shop_id,
            'report_type': self.report_type,
            'report_name': self.report_name,
            'period_type': self.period_type,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'report_data': self.report_data,
            'generated_by': self.generated_by,
            'generation_time': self.generation_time.isoformat() if self.generation_time else None,
            'is_ready': self.is_ready,
            'error_message': self.error_message
        }


class DailyAnalytics(Base):
    """Модель ежедневной аналитики (предварительно агрегированные данные)"""
    __tablename__ = "daily_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Данные о продажах
    total_orders = Column(Integer, default=0)
    total_items_sold = Column(Integer, default=0)
    total_revenue = Column(Numeric(10, 2), default=0)
    total_discount = Column(Numeric(10, 2), default=0)
    average_order_value = Column(Numeric(10, 2), default=0)
    
    # Данные о клиентах
    new_customers = Column(Integer, default=0)
    returning_customers = Column(Integer, default=0)
    
    # Данные о трафике
    total_visits = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    page_views = Column(Integer, default=0)
    bounce_rate = Column(Numeric(5, 2), default=0)
    
    # Данные о конверсии
    conversion_rate = Column(Numeric(5, 2), default=0)
    
    # Популярные товары (формат JSON)
    top_products = Column(JSON, nullable=True)
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    shop = relationship("Shop")
    
    # Индексы
    __table_args__ = (
        Index('ix_daily_analytics_shop_date', 'shop_id', 'date', unique=True),
    )
    
    def __repr__(self):
        return f"<DailyAnalytics(id={self.id}, shop_id={self.shop_id}, date='{self.date.date()}')>"
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь"""
        return {
            'id': self.id,
            'shop_id': self.shop_id,
            'date': self.date.isoformat() if self.date else None,
            'total_orders': self.total_orders,
            'total_items_sold': self.total_items_sold,
            'total_revenue': float(self.total_revenue) if self.total_revenue else 0,
            'total_discount': float(self.total_discount) if self.total_discount else 0,
            'average_order_value': float(self.average_order_value) if self.average_order_value else 0,
            'new_customers': self.new_customers,
            'returning_customers': self.returning_customers,
            'total_visits': self.total_visits,
            'unique_visitors': self.unique_visitors,
            'page_views': self.page_views,
            'bounce_rate': float(self.bounce_rate) if self.bounce_rate else 0,
            'conversion_rate': float(self.conversion_rate) if self.conversion_rate else 0,
            'top_products': self.top_products,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ProductAnalytics(Base):
    """Модель аналитики товаров"""
    __tablename__ = "product_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Данные о просмотрах
    views = Column(Integer, default=0)
    unique_views = Column(Integer, default=0)
    
    # Данные о корзине
    add_to_cart = Column(Integer, default=0)
    remove_from_cart = Column(Integer, default=0)
    
    # Данные о покупках
    purchases = Column(Integer, default=0)
    quantity_sold = Column(Integer, default=0)
    revenue = Column(Numeric(10, 2), default=0)
    
    # Данные о списке желаний
    wishlist_adds = Column(Integer, default=0)
    wishlist_removes = Column(Integer, default=0)
    
    # Коэффициент конверсии
    conversion_rate = Column(Numeric(5, 2), default=0)
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    shop = relationship("Shop")
    product = relationship("Product")
    
    # Индексы
    __table_args__ = (
        Index('ix_product_analytics_shop_product_date', 'shop_id', 'product_id', 'date', unique=True),
    )
    
    def __repr__(self):
        return f"<ProductAnalytics(id={self.id}, product_id={self.product_id}, date='{self.date.date()}')>"
    
    def calculate_conversion_rate(self):
        """Рассчитать коэффициент конверсии"""
        if self.views > 0:
            self.conversion_rate = (self.purchases / self.views) * 100


class TrafficSource(Base):
    """Модель источников трафика"""
    __tablename__ = "traffic_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Информация об источнике
    source_type = Column(String(50), nullable=False, index=True)
    source_name = Column(String(200), nullable=False, index=True)
    campaign = Column(String(200), nullable=True, index=True)
    
    # Данные о трафике
    visits = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    page_views = Column(Integer, default=0)
    avg_session_duration = Column(Integer, default=0)
    
    # Данные о конверсии
    orders = Column(Integer, default=0)
    revenue = Column(Numeric(10, 2), default=0)
    conversion_rate = Column(Numeric(5, 2), default=0)
    
    # Данные о затратах (платный трафик)
    cost = Column(Numeric(10, 2), default=0)
    roi = Column(Numeric(5, 2), default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    shop = relationship("Shop")
    
    # Индексы
    __table_args__ = (
        Index('ix_traffic_sources_shop_date_source', 'shop_id', 'date', 'source_type', 'source_name', unique=True),
    )
    
    def __repr__(self):
        return f"<TrafficSource(id={self.id}, shop_id={self.shop_id}, source='{self.source_name}')>"
    
    def calculate_metrics(self):
        """Рассчитать метрики"""
        # Коэффициент конверсии
        if self.visits > 0:
            self.conversion_rate = (self.orders / self.visits) * 100
        
        # ROI (возврат инвестиций)
        if self.cost > 0:
            self.roi = ((self.revenue - self.cost) / self.cost) * 100