# backend/app/models/shop_settings.py
"""
店铺设置模型
存储店铺的配置和设置信息
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.database import Base


class ShopSettings(Base):
    """Модель настроек магазина (店铺设置)"""
    __tablename__ = "shop_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    
    # 基本店铺信息
    store_name = Column(String(200), nullable=False)
    store_email = Column(String(255), nullable=False)
    store_phone = Column(String(50), nullable=True)

    # 地区和语言设置
    store_currency = Column(String(10), default="CNY")  # 货币代码
    timezone = Column(String(50), default="Asia/Shanghai")  # 时区
    language = Column(String(10), default="zh-CN")  # 语言代码
    
    # 地址信息
    address = Column(JSON, nullable=True, default=dict)
    # {
    #   "country": "中国",
    #   "province": "省份",
    #   "city": "城市",
    #   "district": "区县",
    #   "address_line1": "详细地址1",
    #   "address_line2": "详细地址2",
    #   "postal_code": "邮政编码"
    # }
    
    # 营业时间
    business_hours = Column(JSON, nullable=True, default=list)
    # [
    #   {
    #     "day": "monday",  # 星期几
    #     "open_time": "09:00",
    #     "close_time": "18:00",
    #     "is_open": true
    #   }
    # ]
    
    # 订单设置
    order_settings = Column(JSON, nullable=True, default=dict)
    # {
    #   "minimum_order_amount": 0,  # 最低订单金额
    #   "order_processing_time": 24,  # 订单处理时间(小时)
    #   "order_hold_time": 30,  # 订单保留时间(分钟)
    #   "enable_order_notes": true,  # 启用订单备注
    #   "enable_customer_notifications": true,  # 启用客户通知
    #   "order_confirm_method": "auto",  # auto, manual
    #   "order_number_prefix": "ORD",  # 订单号前缀
    #   "order_number_length": 8,  # 订单号长度
    #   "enable_backorders": false,  # 允许缺货下单
    #   "allow_order_cancellation": true,  # 允许订单取消
    #   "cancellation_time_limit": 60  # 取消时间限制(分钟)
    # }
    
    # 配送设置
    shipping_settings = Column(JSON, nullable=True, default=dict)
    # {
    #   "shipping_methods": [
    #     {
    #       "name": "标准配送",
    #       "code": "standard",
    #       "cost": 0,
    #       "free_shipping_threshold": 99,  # 免邮门槛
    #       "estimated_days": "3-5",
    #       "is_active": true
    #     }
    #   ],
    #   "shipping_zones": [],  # 配送区域
    #   "enable_shipping_calculator": true,  # 启用运费计算器
    #   "handling_fee": 0,  # 处理费
    #   "enable_delivery_date_selection": false,  # 启用配送日期选择
    #   "enable_delivery_time_slots": false  # 启用配送时段选择
    # }
    
    # 支付设置
    payment_settings = Column(JSON, nullable=True, default=dict)
    # {
    #   "payment_methods": [
    #     {
    #       "name": "微信支付",
    #       "code": "wechat_pay",
    #       "is_active": true,
    #       "config": {}  # 支付配置
    #     }
    #   ],
    #   "payment_capture_method": "automatic",  # automatic, manual
    #   "enable_partial_payments": false,  # 启用部分付款
    #   "enable_invoice_generation": true,  # 启用发票生成
    #   "enable_payment_reminders": true,  # 启用付款提醒
    #   "payment_due_days": 7  # 付款到期天数
    # }
    
    # 通知设置
    notification_settings = Column(JSON, nullable=True, default=dict)
    # {
    #   "email_notifications": {
    #     "new_order": true,
    #     "order_shipped": true,
    #     "order_delivered": true,
    #     "low_stock": true,
    #     "new_customer": true
    #   },
    #   "sms_notifications": {
    #     "order_confirmation": false,
    #     "order_shipped": false,
    #     "order_delivered": false
    #   },
    #   "push_notifications": {
    #     "new_order": true,
    #     "new_review": true
    #   },
    #   "notification_templates": {}  # 通知模板
    # }
    
    # SEO设置
    seo_settings = Column(JSON, nullable=True, default=dict)
    # {
    #   "meta_title": "",
    #   "meta_description": "",
    #   "meta_keywords": "",
    #   "social_media_images": {},
    #   "og_tags": {},
    #   "twitter_cards": {},
    #   "structured_data": {},
    #   "sitemap_enabled": true,
    #   "robots_txt": ""
    # }
    
    # 社交媒体
    social_media = Column(JSON, nullable=True, default=dict)
    # {
    #   "facebook": "",
    #   "instagram": "",
    #   "twitter": "",
    #   "wechat": "",
    #   "weibo": "",
    #   "douyin": "",
    #   "xiaohongshu": "",
    #   "linkedin": "",
    #   "youtube": ""
    # }
    
    # 功能开关
    features_enabled = Column(JSON, nullable=True, default=dict)
    # {
    #   "enable_reviews": true,  # 启用评价
    #   "enable_wishlist": true,  # 启用收藏夹
    #   "enable_comparison": true,  # 启用商品比较
    #   "enable_gift_wrapping": true,  # 启用礼品包装
    #   "enable_loyalty_program": false,  # 启用忠诚度计划
    #   "enable_coupons": true,  # 启用优惠券
    #   "enable_gift_cards": true,  # 启用礼品卡
    #   "enable_multiple_addresses": true,  # 启用多个收货地址
    #   "enable_subscriptions": false,  # 启用订阅
    #   "enable_affiliate_program": false  # 启用联盟计划
    # }
    
    # 维护模式
    maintenance_mode = Column(Boolean, default=False)
    maintenance_message = Column(Text, nullable=True)
    
    # 审计字段
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    shop = relationship("Shop", back_populates="settings")
    
    # 索引
    __table_args__ = (
        Index('ix_shop_settings_shop_id', 'shop_id', unique=True),
    )
    
    def __repr__(self):
        return f"<ShopSettings(id={self.id}, shop_id={self.shop_id}, store_name='{self.store_name}')>"
    
    @property
    def is_maintenance(self) -> bool:
        """是否处于维护模式"""
        return self.maintenance_mode
    
    @property
    def formatted_business_hours(self) -> dict:
        """格式化的营业时间"""
        if not self.business_hours:
            return {}
        
        formatted = {}
        for hour in self.business_hours:
            day = hour.get('day')
            if day:
                formatted[day] = {
                    'open_time': hour.get('open_time'),
                    'close_time': hour.get('close_time'),
                    'is_open': hour.get('is_open', True)
                }
        return formatted
    
    @property
    def active_payment_methods(self) -> list:
        """活跃的支付方式"""
        if not self.payment_settings:
            return []
        
        payment_methods = self.payment_settings.get('payment_methods', [])
        return [method for method in payment_methods if method.get('is_active', False)]
    
    @property
    def active_shipping_methods(self) -> list:
        """活跃的配送方式"""
        if not self.shipping_settings:
            return []
        
        shipping_methods = self.shipping_settings.get('shipping_methods', [])
        return [method for method in shipping_methods if method.get('is_active', False)]
    
    def get_feature_status(self, feature_name: str) -> bool:
        """获取功能状态"""
        if not self.features_enabled:
            return False
        return self.features_enabled.get(feature_name, False)
    
    def enable_feature(self, feature_name: str, enabled: bool = True):
        """启用或禁用功能"""
        if not self.features_enabled:
            self.features_enabled = {}
        self.features_enabled[feature_name] = enabled
    
    def add_shipping_method(self, shipping_method: dict):
        """添加配送方式"""
        if not self.shipping_settings:
            self.shipping_settings = {}
        
        if 'shipping_methods' not in self.shipping_settings:
            self.shipping_settings['shipping_methods'] = []
        
        self.shipping_settings['shipping_methods'].append(shipping_method)
    
    def add_payment_method(self, payment_method: dict):
        """添加支付方式"""
        if not self.payment_settings:
            self.payment_settings = {}
        
        if 'payment_methods' not in self.payment_settings:
            self.payment_settings['payment_methods'] = []
        
        self.payment_settings['payment_methods'].append(payment_method)
    
    def to_dict(self, include_relations: bool = False) -> dict:
        """转换为字典"""
        result = {
            'id': self.id,
            'shop_id': self.shop_id,
            'store_name': self.store_name,
            'store_email': self.store_email,
            'store_phone': self.store_phone,
            'store_currency': self.store_currency,
            'timezone': self.timezone,
            'language': self.language,
            'address': self.address or {},
            'business_hours': self.business_hours or [],
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
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_maintenance': self.is_maintenance,
            'formatted_business_hours': self.formatted_business_hours,
            'active_payment_methods': self.active_payment_methods,
            'active_shipping_methods': self.active_shipping_methods
        }
        
        if include_relations:
            result['shop'] = {
                'id': self.shop.id,
                'name': self.shop.name
            } if self.shop else None
        
        return result
