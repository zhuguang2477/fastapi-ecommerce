# backend/app/models/shop_setting.py
"""
店铺设置模型
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, Numeric, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.database import Base


class ShopSettings(Base):
    """Модель настроек магазина"""
    __tablename__ = "shop_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, unique=True, index=True)
    
    # Общие настройки
    store_name = Column(String(200), nullable=False)
    store_email = Column(String(255), nullable=False)
    store_phone = Column(String(50), nullable=True)
    store_currency = Column(String(10), default="CNY")
    timezone = Column(String(50), default="Asia/Shanghai")
    language = Column(String(10), default="zh_CN")
    
    # Настройки адреса
    address = Column(JSON, nullable=True)  # Адрес магазина
    
    # Часы работы
    business_hours = Column(JSON, nullable=True)  # Конфигурация часов работы
    
    # Настройки заказов
    order_settings = Column(JSON, nullable=True, default=dict)
    # {
    #   "auto_confirm_orders": false,
    #   "hold_stock_minutes": 30,
    #   "allow_partial_payments": false,
    #   "minimum_order_amount": 0,
    #   "tax_included": true,
    #   "tax_rate": 0.13
    # }
    
    # Настройки доставки
    shipping_settings = Column(JSON, nullable=True, default=dict)
    # {
    #   "shipping_methods": ["standard", "express"],
    #   "free_shipping_threshold": 100,
    #   "shipping_zones": [...]
    # }
    
    # Настройки оплаты
    payment_settings = Column(JSON, nullable=True, default=dict)
    # {
    #   "payment_methods": ["wechat_pay", "alipay", "cash_on_delivery"],
    #   "auto_capture_payments": true
    # }
    
    # Настройки уведомлений
    notification_settings = Column(JSON, nullable=True, default=dict)
    
    # SEO настройки
    seo_settings = Column(JSON, nullable=True, default=dict)
    
    # Социальные сети
    social_media = Column(JSON, nullable=True, default=dict)
    
    # Расширенные функции
    features_enabled = Column(JSON, nullable=True, default=dict)
    # {
    #   "multi_currency": false,
    #   "multi_language": false,
    #   "gift_cards": false,
    #   "loyalty_program": false
    # }
    
    # Режим обслуживания
    maintenance_mode = Column(Boolean, default=False)
    maintenance_message = Column(Text, nullable=True)
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    shop = relationship("Shop", back_populates="settings")
    
    def __repr__(self):
        return f"<ShopSettings(id={self.id}, shop_id={self.shop_id})>"
    
    def get_setting(self, key_path, default=None):
        """Получить вложенные настройки"""
        import jsonpath_rw
        
        try:
            jsonpath_expr = jsonpath_rw.parse(key_path)
            matches = [match.value for match in jsonpath_expr.find(self.to_dict())]
            return matches[0] if matches else default
        except:
            return default
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь"""
        return {
            'id': self.id,
            'shop_id': self.shop_id,
            'store_name': self.store_name,
            'store_email': self.store_email,
            'store_phone': self.store_phone,
            'store_currency': self.store_currency,
            'timezone': self.timezone,
            'language': self.language,
            'address': self.address,
            'business_hours': self.business_hours,
            'order_settings': self.order_settings or {},
            'shipping_settings': self.shipping_settings or {},
            'payment_settings': self.payment_settings or {},
            'notification_settings': self.notification_settings or {},
            'seo_settings': self.seo_settings or {},
            'social_media': self.social_media or {},
            'features_enabled': self.features_enabled or {},
            'maintenance_mode': self.maintenance_mode,
            'maintenance_message': self.maintenance_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ShopDesign(Base):
    """Модель дизайна магазина"""
    __tablename__ = "shop_designs"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, unique=True, index=True)
    
    # Настройки темы
    theme_name = Column(String(100), default="default")
    color_scheme = Column(JSON, nullable=True, default=dict)
    # {
    #   "primary": "#4CAF50",
    #   "secondary": "#2196F3",
    #   "accent": "#FF9800",
    #   "background": "#FFFFFF",
    #   "text": "#333333"
    # }
    
    # Настройки шрифтов
    font_settings = Column(JSON, nullable=True, default=dict)
    
    # Настройки макета
    layout_settings = Column(JSON, nullable=True, default=dict)
    
    # Шапка и подвал
    header_settings = Column(JSON, nullable=True, default=dict)
    footer_settings = Column(JSON, nullable=True, default=dict)
    
    # Настройки главной страницы
    homepage_settings = Column(JSON, nullable=True, default=dict)
    
    # Настройки страницы товара
    product_page_settings = Column(JSON, nullable=True, default=dict)
    
    # Пользовательские CSS/JS
    custom_css = Column(Text, nullable=True)
    custom_js = Column(Text, nullable=True)
    
    # Логотип и изображения
    logo_url = Column(String(500), nullable=True)
    favicon_url = Column(String(500), nullable=True)
    banner_images = Column(JSON, nullable=True)  # Изображения баннеров
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    shop = relationship("Shop", back_populates="design")
    
    def __repr__(self):
        return f"<ShopDesign(id={self.id}, shop_id={self.shop_id})>"
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь"""
        return {
            'id': self.id,
            'shop_id': self.shop_id,
            'theme_name': self.theme_name,
            'color_scheme': self.color_scheme or {},
            'font_settings': self.font_settings or {},
            'layout_settings': self.layout_settings or {},
            'header_settings': self.header_settings or {},
            'footer_settings': self.footer_settings or {},
            'homepage_settings': self.homepage_settings or {},
            'product_page_settings': self.product_page_settings or {},
            'custom_css': self.custom_css,
            'custom_js': self.custom_js,
            'logo_url': self.logo_url,
            'favicon_url': self.favicon_url,
            'banner_images': self.banner_images,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }