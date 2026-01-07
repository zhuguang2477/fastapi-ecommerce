from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, Dict, Any, List
from datetime import datetime

class ShopAddress(BaseModel):
    """店铺地址信息"""
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None

class BusinessHours(BaseModel):
    """营业时间"""
    day: str  # monday, tuesday, etc.
    open_time: str
    close_time: str
    is_open: bool = True

class ShippingMethod(BaseModel):
    """配送方式"""
    name: str
    code: str
    cost: float = 0
    free_shipping_threshold: Optional[float] = None
    estimated_days: str
    is_active: bool = True

class PaymentMethod(BaseModel):
    """支付方式"""
    name: str
    code: str
    is_active: bool = True
    config: Dict[str, Any] = {}

class NotificationConfig(BaseModel):
    """通知配置"""
    email_notifications: Dict[str, bool] = {}
    sms_notifications: Dict[str, bool] = {}
    push_notifications: Dict[str, bool] = {}
    notification_templates: Dict[str, str] = {}

class SEOSettings(BaseModel):
    """SEO设置"""
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    social_media_images: Dict[str, str] = {}
    og_tags: Dict[str, str] = {}
    twitter_cards: Dict[str, str] = {}
    structured_data: Dict[str, Any] = {}
    sitemap_enabled: bool = True
    robots_txt: str = ""

class ShopSettingsBase(BaseModel):
    """Базовая информация о настройках магазина"""
    store_name: Optional[str] = Field(None, max_length=200, description="店铺名称")
    store_email: Optional[EmailStr] = Field(None, description="店铺邮箱")
    store_phone: Optional[str] = Field(None, max_length=20, description="店铺电话")
    store_currency: Optional[str] = Field("CNY", max_length=3, description="货币代码")
    timezone: Optional[str] = Field("Asia/Shanghai", description="时区")
    language: Optional[str] = Field("zh-CN", description="语言代码")
    
    @validator('store_phone')
    def validate_phone(cls, v):
        if v and not v.replace('+', '').replace(' ', '').replace('-', '').isdigit():
            raise ValueError('Invalid phone number format')
        return v
    
    @validator('store_currency')
    def validate_currency(cls, v):
        if v and len(v) != 3:
            raise ValueError('Currency code must be 3 characters')
        return v.upper() if v else v

class ShopSettingsCreate(ShopSettingsBase):
    """创建店铺设置"""
    shop_id: int = Field(..., description="店铺ID")
    address: Optional[Dict[str, Any]] = Field(None, description="地址信息")
    business_hours: Optional[List[Dict[str, Any]]] = Field(None, description="营业时间")
    order_settings: Optional[Dict[str, Any]] = Field(None, description="订单设置")
    shipping_settings: Optional[Dict[str, Any]] = Field(None, description="配送设置")
    payment_settings: Optional[Dict[str, Any]] = Field(None, description="支付设置")
    notification_settings: Optional[Dict[str, Any]] = Field(None, description="通知设置")
    seo_settings: Optional[Dict[str, Any]] = Field(None, description="SEO设置")
    social_media: Optional[Dict[str, Any]] = Field(None, description="社交媒体")
    features_enabled: Optional[Dict[str, Any]] = Field(None, description="功能开关")

class ShopSettingsUpdate(BaseModel):
    """更新店铺设置"""
    store_name: Optional[str] = Field(None, max_length=200)
    store_email: Optional[EmailStr] = None
    store_phone: Optional[str] = Field(None, max_length=20)
    store_currency: Optional[str] = Field(None, max_length=3)
    timezone: Optional[str] = None
    language: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    business_hours: Optional[List[Dict[str, Any]]] = None
    order_settings: Optional[Dict[str, Any]] = None
    shipping_settings: Optional[Dict[str, Any]] = None
    payment_settings: Optional[Dict[str, Any]] = None
    notification_settings: Optional[Dict[str, Any]] = None
    seo_settings: Optional[Dict[str, Any]] = None
    social_media: Optional[Dict[str, Any]] = None
    features_enabled: Optional[Dict[str, Any]] = None
    maintenance_mode: Optional[bool] = None
    maintenance_message: Optional[str] = None

class ShopSettingsResponse(ShopSettingsBase):
    """店铺设置响应"""
    id: int = Field(..., description="设置ID")
    shop_id: int = Field(..., description="店铺ID")
    address: Dict[str, Any] = Field(default_factory=dict, description="地址信息")
    business_hours: List[Dict[str, Any]] = Field(default_factory=list, description="营业时间")
    order_settings: Dict[str, Any] = Field(default_factory=dict, description="订单设置")
    shipping_settings: Dict[str, Any] = Field(default_factory=dict, description="配送设置")
    payment_settings: Dict[str, Any] = Field(default_factory=dict, description="支付设置")
    notification_settings: Dict[str, Any] = Field(default_factory=dict, description="通知设置")
    seo_settings: Dict[str, Any] = Field(default_factory=dict, description="SEO设置")
    social_media: Dict[str, Any] = Field(default_factory=dict, description="社交媒体")
    features_enabled: Dict[str, Any] = Field(default_factory=dict, description="功能开关")
    maintenance_mode: bool = Field(False, description="维护模式")
    maintenance_message: Optional[str] = Field(None, description="维护消息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

class ShopSettingsDefault(BaseModel):
    """默认店铺设置"""
    store_name: Optional[str] = None
    store_email: Optional[EmailStr] = None
    store_phone: Optional[str] = None
    address: Dict[str, Any] = {}
    store_currency: str = "CNY"
    timezone: str = "Asia/Shanghai"
    language: str = "zh-CN"
    business_hours: List[Dict[str, Any]] = []
    order_settings: Dict[str, Any] = {
        "minimum_order_amount": 0,
        "order_processing_time": 24,
        "order_hold_time": 30,
        "enable_order_notes": True,
        "enable_customer_notifications": True,
        "order_confirm_method": "auto"
    }
    shipping_settings: Dict[str, Any] = {
        "shipping_methods": [],
        "enable_shipping_calculator": True,
        "handling_fee": 0
    }
    payment_settings: Dict[str, Any] = {
        "payment_methods": [],
        "payment_capture_method": "automatic"
    }
    notification_settings: Dict[str, Any] = {
        "email_notifications": {
            "new_order": True,
            "order_shipped": True,
            "order_delivered": True
        }
    }
    seo_settings: Dict[str, Any] = {}
    social_media: Dict[str, Any] = {}
    features_enabled: Dict[str, Any] = {
        "enable_reviews": True,
        "enable_wishlist": True,
        "enable_coupons": True
    }
    maintenance_mode: bool = False
    maintenance_message: Optional[str] = None
    
    class Config:
        from_attributes = True