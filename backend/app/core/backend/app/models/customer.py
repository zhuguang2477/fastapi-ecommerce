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
    display_name = Column(String(100), nullable=True)  # Отображаемое имя
    avatar_url = Column(String(500), nullable=True)
    
    orders = relationship("Order", back_populates="customer")

    # Контактная информация
    contact_info = Column(JSON, nullable=True, default=dict)  # Контактная информация в JSON
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
    addresses = Column(JSON, nullable=True, default=list)  # Список адресов в JSON
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
    customer_type = Column(String(50), default="regular")  # regular, vip, wholesale
    customer_group = Column(String(100), nullable=True)    # Группа клиентов
    tags = Column(JSON, nullable=True)  # Теги клиента
    
    # Статус
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Проверка email/телефона
    is_newsletter_subscribed = Column(Boolean, default=False)  # Подписка на рассылку
    
    # Информация об аккаунте
    account_balance = Column(Numeric(10, 2), default=0)  # Баланс счета (может использоваться для списания)
    credit_limit = Column(Numeric(10, 2), default=0)     # Кредитный лимит
    
    # Статистическая информация (регулярно обновляется)
    total_orders = Column(Integer, default=0)
    total_spent = Column(Numeric(10, 2), default=0)
    average_order_value = Column(Numeric(10, 2), default=0)
    first_order_date = Column(DateTime(timezone=True), nullable=True)
    last_order_date = Column(DateTime(timezone=True), nullable=True)
    
    # Пожизненная ценность клиента
    clv = Column(Numeric(10, 2), default=0)  # Customer Lifetime Value
    
    # Маркетинговая информация
    source = Column(String(100), nullable=True)  # Источник клиента
    referral_code = Column(String(100), nullable=True, index=True)  # Реферальный код
    referred_by = Column(Integer, ForeignKey("customers.id"), nullable=True)  # Реферер
    
    # Примечания
    notes = Column(Text, nullable=True)  # Примечания к клиенту
    
    # Временные метки
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи - используем строки чтобы избежать циклического импорта
    shop = relationship("Shop", back_populates="customers")
    
    # Внимание: не определяем связь orders здесь, чтобы избежать циклического импорта
    # Мы будем обрабатывать связь с заказами динамически
    # orders = relationship("Order", back_populates="customer")  # Закомментированная строка
    
    referred_customers = relationship("Customer", backref="referrer", remote_side=[id])
    
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
    
    def update_statistics(self, db_session):
        """Обновить статистические данные клиента"""
        from sqlalchemy import func
        
        # Динамический импорт, чтобы избежать циклического импорта
        try:
            from backend.app.models.order import Order
        except ImportError:
            # Попробовать относительный импорт
            try:
                from .order import Order
            except ImportError:
                # Если ничего не работает, просто вернуться
                print("Предупреждение: не удалось импортировать модель Order")
                return
        
        # Получить статистику заказов
        stats = db_session.query(
            func.count(Order.id).label('total_orders'),
            func.sum(Order.total_amount).label('total_spent'),
            func.min(Order.created_at).label('first_order_date'),
            func.max(Order.created_at).label('last_order_date')
        ).filter(
            Order.customer_id == self.id,
            Order.status != 'cancelled'
        ).first()
        
        if stats:
            self.total_orders = stats.total_orders or 0
            self.total_spent = stats.total_spent or 0
            self.first_order_date = stats.first_order_date
            self.last_order_date = stats.last_order_date
            
            # Рассчитать среднюю стоимость заказа
            if self.total_orders > 0:
                self.average_order_value = self.total_spent / self.total_orders
            
            # Простой расчет CLV (можно настроить в соответствии с бизнес-требованиями)
            self.clv = self.total_spent * 1.5  # Предположим, что CLV в 1.5 раза больше общей суммы расходов
    
    def to_dict(self, include_relations: bool = False, db_session=None) -> dict:
        """Преобразовать в словарь"""
        result = {
            'id': self.id,
            'shop_id': self.shop_id,
            'email': self.email,
            'phone': self.phone,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'display_name': self.display_name,
            'avatar_url': self.avatar_url,
            'contact_info': self.contact_info or {},
            'addresses': self.addresses or [],
            'customer_type': self.customer_type,
            'customer_group': self.customer_group,
            'tags': self.tags,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'is_newsletter_subscribed': self.is_newsletter_subscribed,
            'account_balance': float(self.account_balance) if self.account_balance else 0,
            'credit_limit': float(self.credit_limit) if self.credit_limit else 0,
            'total_orders': self.total_orders,
            'total_spent': float(self.total_spent) if self.total_spent else 0,
            'average_order_value': float(self.average_order_value) if self.average_order_value else 0,
            'clv': float(self.clv) if self.clv else 0,
            'source': self.source,
            'referral_code': self.referral_code,
            'referred_by': self.referred_by,
            'notes': self.notes,
            'is_vip': self.is_vip,
            'default_shipping_address': self.default_shipping_address,
            'default_billing_address': self.default_billing_address,
            'registered_at': self.registered_at.isoformat() if self.registered_at else None,
            'last_active_at': self.last_active_at.isoformat() if self.last_active_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_relations and db_session:
            # Динамический импорт Order, чтобы избежать циклического импорта
            try:
                from backend.app.models.order import Order as OrderModel
                
                # Получить последние заказы
                recent_orders = db_session.query(OrderModel).filter(
                    OrderModel.customer_id == self.id
                ).order_by(OrderModel.created_at.desc()).limit(5).all()
                
                if recent_orders:
                    result['recent_orders'] = [
                        {
                            'id': order.id,
                            'order_number': order.order_number,
                            'order_date': order.created_at.isoformat() if order.created_at else None,
                            'total_amount': float(order.total_amount) if order.total_amount else 0,
                            'status': order.status
                        }
                        for order in recent_orders
                    ]
            except ImportError:
                pass
        
        return result


class CustomerNote(Base):
    """Модель примечаний к клиенту"""
    __tablename__ = "customer_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    
    # Содержимое примечания
    content = Column(Text, nullable=False)
    note_type = Column(String(50), default="general")  # general, support, follow_up, etc.
    is_important = Column(Boolean, default=False)
    
    # Информация о создателе
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # ID сотрудника
    created_by_name = Column(String(100), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    customer = relationship("Customer")
    shop = relationship("Shop")
    creator = relationship("User")
    
    def __repr__(self):
        return f"<CustomerNote(id={self.id}, customer_id={self.customer_id})>"