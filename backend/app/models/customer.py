# backend/app/models/customer.py
"""
客户模型
聚合客户数据和统计信息
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, Numeric, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.database import Base


class Customer(Base):
    """Модель клиента (агрегированные данные)"""
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    
    # Основная информация
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=True, index=True)
    
    # Персональная информация
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    display_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Контактная информация
    contact_info = Column(JSON, nullable=True, default=dict)
    # {
    #   "company": "Название компании",
    #   "job_title": "Должность",
    #   "website": "Веб-сайт",
    #   "social_media": {
    #     "wechat": "WeChat ID",
    #     "qq": "QQ номер",
    #     "weibo": "Weibo"
    #   }
    # }
    
    # Адресная информация (агрегированная)
    addresses = Column(JSON, nullable=True, default=list)
    # [
    #   {
    #     "type": "shipping" | "billing",
    #     "name": "Получатель",
    #     "phone": "Телефон",
    #     "address_line1": "Адрес 1",
    #     "address_line2": "Адрес 2",
    #     "city": "Город",
    #     "state": "Провинция",
    #     "postal_code": "Почтовый индекс",
    #     "country": "Страна",
    #     "is_default": true
    #   }
    # ]
    
    # Классификация клиентов
    customer_type = Column(String(50), default="regular")
    customer_group = Column(String(100), nullable=True)
    tags = Column(JSON, nullable=True)
    
    # Статус
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_newsletter_subscribed = Column(Boolean, default=False)
    
    # Информация об аккаунте
    account_balance = Column(Numeric(10, 2), default=0)
    credit_limit = Column(Numeric(10, 2), default=0)
    
    # Статистическая информация (регулярно обновляется)
    total_orders = Column(Integer, default=0)
    total_spent = Column(Numeric(10, 2), default=0)
    average_order_value = Column(Numeric(10, 2), default=0)
    first_order_date = Column(DateTime(timezone=True), nullable=True)
    last_order_date = Column(DateTime(timezone=True), nullable=True)
    
    # Пожизненная ценность клиента
    clv = Column(Numeric(10, 2), default=0)
    
    # Маркетинговая информация
    source = Column(String(100), nullable=True)
    referral_code = Column(String(100), nullable=True, index=True)
    referred_by = Column(Integer, ForeignKey("customers.id"), nullable=True)
    
    # Примечания
    notes = Column(Text, nullable=True)
    
    # Временные метки
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    shop = relationship("Shop", back_populates="customers")
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    referred_customers = relationship("Customer", backref="referrer", remote_side=[id])
    recipients = relationship("Recipient", back_populates="customer", cascade="all, delete-orphan")
    basket = relationship("Basket", back_populates="customer", uselist=False, cascade="all, delete-orphan")
    notes = relationship("CustomerNote", back_populates="customer", cascade="all, delete-orphan")
    
    # Индексы
    __table_args__ = (
        Index('ix_customers_shop_email', 'shop_id', 'email'),
        Index('ix_customers_shop_phone', 'shop_id', 'phone'),
        Index('ix_customers_shop_type', 'shop_id', 'customer_type'),
    )
    
    def __repr__(self):
        return f"<Customer(id={self.id}, email='{self.email}', shop_id={self.shop_id})>"
    
    @property
    def full_name(self) -> str:
        """Получить полное имя"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.display_name or self.email
    
    @property
    def is_vip(self) -> bool:
        """Является ли клиент VIP"""
        return self.customer_type == "vip"
    
    @property
    def default_shipping_address(self) -> dict:
        """Получить адрес доставки по умолчанию"""
        if not self.addresses:
            return None
        
        for address in self.addresses:
            if address.get('type') == 'shipping' and address.get('is_default'):
                return address
        
        # Если нет адреса по умолчанию, возвращаем первый адрес доставки
        for address in self.addresses:
            if address.get('type') == 'shipping':
                return address
        
        return None
    
    @property
    def default_billing_address(self) -> dict:
        """Получить платежный адрес по умолчанию"""
        if not self.addresses:
            return None
        
        for address in self.addresses:
            if address.get('type') == 'billing' and address.get('is_default'):
                return address
        
        # Если нет адреса по умолчанию, возвращаем первый платежный адрес
        for address in self.addresses:
            if address.get('type') == 'billing':
                return address
        
        return None
    
    def to_dict(self, include_relations: bool = False) -> dict:
        """Преобразовать в словарь"""
        result = {
            'id': self.id,
            'shop_id': self.shop_id,
            'email': self.email,
            'phone': self.phone,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'display_name': self.display_name,
            'full_name': self.full_name,
            'avatar_url': self.avatar_url,
            'contact_info': self.contact_info or {},
            'addresses': self.addresses or [],
            'customer_type': self.customer_type,
            'customer_group': self.customer_group,
            'tags': self.tags or [],
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'is_newsletter_subscribed': self.is_newsletter_subscribed,
            'account_balance': float(self.account_balance) if self.account_balance else 0,
            'credit_limit': float(self.credit_limit) if self.credit_limit else 0,
            'total_orders': self.total_orders,
            'total_spent': float(self.total_spent) if self.total_spent else 0,
            'average_order_value': float(self.average_order_value) if self.average_order_value else 0,
            'first_order_date': self.first_order_date.isoformat() if self.first_order_date else None,
            'last_order_date': self.last_order_date.isoformat() if self.last_order_date else None,
            'clv': float(self.clv) if self.clv else 0,
            'source': self.source,
            'referral_code': self.referral_code,
            'referred_by': self.referred_by,
            'notes': self.notes,
            'registered_at': self.registered_at.isoformat() if self.registered_at else None,
            'last_active_at': self.last_active_at.isoformat() if self.last_active_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_relations:
            result['shop'] = {
                'id': self.shop.id,
                'name': self.shop.name
            } if self.shop else None
            
            result['orders_count'] = len(self.orders) if self.orders else 0
            result['recipients_count'] = len(self.recipients) if self.recipients else 0
            result['has_basket'] = bool(self.basket)
        
        return result