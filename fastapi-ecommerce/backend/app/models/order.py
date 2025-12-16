# backend/app/models/order.py
"""
订单模型
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, Numeric, JSON, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from backend.app.database import Base


class OrderStatus(enum.Enum):
    """Перечисление статусов заказа"""
    PENDING = "pending"           # В ожидании
    CONFIRMED = "confirmed"       # Подтвержден
    PROCESSING = "processing"     # В обработке
    SHIPPED = "shipped"           # Отправлен
    DELIVERED = "delivered"       # Доставлен
    CANCELLED = "cancelled"       # Отменен
    REFUNDED = "refunded"         # Возвращен
    FAILED = "failed"             # Неудачный


class PaymentStatus(enum.Enum):
    """Перечисление статусов оплаты"""
    PENDING = "pending"           # Ожидает оплаты
    AUTHORIZED = "authorized"     # Авторизован
    PAID = "paid"                 # Оплачен
    PARTIALLY_PAID = "partially_paid"  # Частично оплачен
    REFUNDED = "refunded"         # Возвращен
    VOIDED = "voided"             # Аннулирован
    FAILED = "failed"             # Ошибка оплаты


class PaymentMethod(enum.Enum):
    """Перечисление способов оплаты"""
    CASH = "cash"                 # Наличные
    CARD = "card"                 # Кредитная/дебетовая карта
    WECHAT_PAY = "wechat_pay"     # WeChat Pay
    ALIPAY = "alipay"             # Alipay
    BANK_TRANSFER = "bank_transfer"  # Банковский перевод
    PAYPAL = "paypal"             # PayPal
    OTHER = "other"               # Другое


class ShippingMethod(enum.Enum):
    """Перечисление способов доставки"""
    STANDARD = "standard"         # Стандартная доставка
    EXPRESS = "express"           # Экспресс-доставка
    PICKUP = "pickup"             # Самовывоз
    DIGITAL = "digital"           # Цифровая доставка (виртуальные товары)


class Order(Base):
    """Модель заказа"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    
    # Информация о заказе
    order_number = Column(String(50), unique=True, nullable=False, index=True)  # Номер заказа, например "ORD-20231215-001"
    order_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Информация о клиенте
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    customer_email = Column(String(255), nullable=False, index=True)
    customer_phone = Column(String(50), nullable=True)
    
    # Данные клиента (формат JSON, агрегированные данные, чтобы избежать частых запросов)
    customer_data = Column(JSON, nullable=True, default=dict)  # Пример структуры:
    # {
    #   "name": "Иван Иванов",
    #   "email": "ivan@example.com",
    #   "phone": "+79001234567",
    #   "shipping_address": {...},
    #   "billing_address": {...},
    #   "notes": "Примечания клиента"
    # }
    
    # Статусы
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, index=True)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, index=True)
    
    # Информация об оплате
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    payment_reference = Column(String(100), nullable=True, index=True)  # Референтный номер оплаты
    payment_date = Column(DateTime(timezone=True), nullable=True)
    
    # Финансовая информация
    subtotal = Column(Numeric(10, 2), nullable=False, default=0)  # Подытог по товарам
    tax_amount = Column(Numeric(10, 2), nullable=False, default=0)  # Налоги
    shipping_amount = Column(Numeric(10, 2), nullable=False, default=0)  # Стоимость доставки
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)  # Скидка
    tip_amount = Column(Numeric(10, 2), nullable=False, default=0)  # Чаевые
    total_amount = Column(Numeric(10, 2), nullable=False, default=0)  # Итоговая сумма
    
    # Валюта
    currency = Column(String(10), default="CNY")  # Код валюты
    
    # Информация о доставке
    shipping_method = Column(Enum(ShippingMethod), nullable=True)
    shipping_tracking_number = Column(String(100), nullable=True, index=True)
    shipping_carrier = Column(String(100), nullable=True)
    estimated_delivery_date = Column(DateTime(timezone=True), nullable=True)
    actual_delivery_date = Column(DateTime(timezone=True), nullable=True)
    
    # Адресная информация (формат JSON)
    shipping_address = Column(JSON, nullable=True)  # Адрес доставки
    billing_address = Column(JSON, nullable=True)   # Адрес для выставления счета
    
    # Примечания
    customer_notes = Column(Text, nullable=True)  # Примечания клиента
    staff_notes = Column(Text, nullable=True)     # Примечания сотрудников
    
    # Маркетинговая информация
    marketing_source = Column(String(100), nullable=True)  # Маркетинговый источник
    referral_code = Column(String(100), nullable=True)     # Реферальный код
    coupon_code = Column(String(100), nullable=True, index=True)  # Код купона
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    shop = relationship("Shop", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    # Индексы
    __table_args__ = (
        Index('ix_orders_shop_date', 'shop_id', 'order_date'),
        Index('ix_orders_shop_status', 'shop_id', 'status'),
        Index('ix_orders_customer_shop', 'customer_id', 'shop_id'),
    )
    
    def __repr__(self):
        return f"<Order(id={self.id}, order_number='{self.order_number}', shop_id={self.shop_id})>"
    
    @property
    def item_count(self) -> int:
        """Количество товаров в заказе"""
        return sum(item.quantity for item in self.items)
    
    @property
    def customer_name(self) -> str:
        """Получить имя клиента"""
        if self.customer_data and 'name' in self.customer_data:
            return self.customer_data['name']
        elif self.customer:
            return self.customer.full_name
        return self.customer_email
    
    @property
    def is_paid(self) -> bool:
        """Оплачен ли заказ"""
        return self.payment_status in [PaymentStatus.PAID, PaymentStatus.AUTHORIZED]
    
    @property
    def is_delivered(self) -> bool:
        """Доставлен ли заказ"""
        return self.status == OrderStatus.DELIVERED
    
    def calculate_totals(self):
        """Пересчитать итоговые суммы заказа"""
        # Подытог по товарам
        self.subtotal = sum(item.total_price for item in self.items)
        
        # Итог = подытог + налоги + стоимость доставки + чаевые - скидка
        self.total_amount = (
            self.subtotal +
            self.tax_amount +
            self.shipping_amount +
            self.tip_amount -
            self.discount_amount
        )
    
    def to_dict(self, include_relations: bool = False) -> dict:
        """Преобразовать в словарь"""
        result = {
            'id': self.id,
            'shop_id': self.shop_id,
            'order_number': self.order_number,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'customer_id': self.customer_id,
            'customer_email': self.customer_email,
            'customer_phone': self.customer_phone,
            'customer_name': self.customer_name,
            'customer_data': self.customer_data or {},
            'status': self.status.value,
            'payment_status': self.payment_status.value,
            'payment_method': self.payment_method.value if self.payment_method else None,
            'payment_reference': self.payment_reference,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'subtotal': float(self.subtotal) if self.subtotal else 0,
            'tax_amount': float(self.tax_amount) if self.tax_amount else 0,
            'shipping_amount': float(self.shipping_amount) if self.shipping_amount else 0,
            'discount_amount': float(self.discount_amount) if self.discount_amount else 0,
            'tip_amount': float(self.tip_amount) if self.tip_amount else 0,
            'total_amount': float(self.total_amount) if self.total_amount else 0,
            'currency': self.currency,
            'shipping_method': self.shipping_method.value if self.shipping_method else None,
            'shipping_tracking_number': self.shipping_tracking_number,
            'shipping_carrier': self.shipping_carrier,
            'estimated_delivery_date': self.estimated_delivery_date.isoformat() if self.estimated_delivery_date else None,
            'actual_delivery_date': self.actual_delivery_date.isoformat() if self.actual_delivery_date else None,
            'shipping_address': self.shipping_address,
            'billing_address': self.billing_address,
            'customer_notes': self.customer_notes,
            'staff_notes': self.staff_notes,
            'marketing_source': self.marketing_source,
            'referral_code': self.referral_code,
            'coupon_code': self.coupon_code,
            'item_count': self.item_count,
            'is_paid': self.is_paid,
            'is_delivered': self.is_delivered,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_relations:
            if self.items:
                result['items'] = [
                    {
                        'id': item.id,
                        'product_id': item.product_id,
                        'product_name': item.product_name,
                        'variant_name': item.variant_name,
                        'quantity': item.quantity,
                        'unit_price': float(item.unit_price) if item.unit_price else 0,
                        'total_price': float(item.total_price) if item.total_price else 0
                    }
                    for item in self.items
                ]
        
        return result


class OrderItem(Base):
    """Модель позиции заказа"""
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=True, index=True)
    
    # Информация о товаре (снимок, чтобы избежать влияния изменений товара на заказ)
    product_name = Column(String(200), nullable=False)
    product_sku = Column(String(100), nullable=True)
    variant_name = Column(String(200), nullable=True)
    variant_attributes = Column(JSON, nullable=True)  # Атрибуты варианта
    
    # Цена и количество
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    # Скидка
    discount_amount = Column(Numeric(10, 2), default=0)
    
    # Снимок товара (формат JSON, сохраняет информацию о товаре на момент заказа)
    product_snapshot = Column(JSON, nullable=True)
    
    # Связи
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    variant = relationship("ProductVariant", back_populates="order_items")
    
    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product_name='{self.product_name}')>"
    
    @property
    def display_name(self) -> str:
        """Отображаемое название"""
        if self.variant_name:
            return f"{self.product_name} - {self.variant_name}"
        return self.product_name
    
    def calculate_total(self):
        """Вычислить общую стоимость"""
        self.total_price = self.unit_price * self.quantity - self.discount_amount