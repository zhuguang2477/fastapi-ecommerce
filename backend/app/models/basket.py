# backend/app/models/basket.py
"""
购物车模型
代表用户的购物车，存储未结算的商品
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, Numeric, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum

from backend.app.database import Base


class BasketStatus(PyEnum):
    """购物车状态枚举"""
    ACTIVE = "active"
    ABANDONED = "abandoned"
    CONVERTED = "converted"
    EXPIRED = "expired"


class Basket(Base):
    """Модель корзины (购物车)"""
    __tablename__ = "baskets"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    
    # 购物车标识
    basket_token = Column(String(100), nullable=False, unique=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    
    # 状态信息
    status = Column(String(20), default=BasketStatus.ACTIVE.value)
    is_guest = Column(Boolean, default=False)
    
    # 价格信息
    subtotal = Column(Numeric(10, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    shipping_amount = Column(Numeric(10, 2), default=0)
    tax_amount = Column(Numeric(10, 2), default=0)
    total_amount = Column(Numeric(10, 2), default=0)
    
    # 货币信息
    currency = Column(String(10), default="CNY")
    
    # 优惠信息
    coupon_code = Column(String(100), nullable=True, index=True)
    discount_rules = Column(JSON, nullable=True)
    
    # 配送信息
    shipping_method = Column(String(100), nullable=True)
    shipping_address_id = Column(Integer, ForeignKey("recipients.id"), nullable=True)
    
    # 时间信息
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # 元数据 - 修改字段名避免冲突
    basket_metadata = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    
    # 关系
    shop = relationship("Shop", back_populates="baskets")
    customer = relationship("Customer", back_populates="basket")
    items = relationship("BasketItem", back_populates="basket", cascade="all, delete-orphan")
    shipping_address = relationship("Recipient", foreign_keys=[shipping_address_id])
    
    # 索引
    __table_args__ = (
        Index('ix_baskets_customer_status', 'customer_id', 'status'),
        Index('ix_baskets_shop_status', 'shop_id', 'status'),
        Index('ix_baskets_token_status', 'basket_token', 'status'),
        Index('ix_baskets_last_activity', 'last_activity_at'),
    )
    
    def __repr__(self):
        return f"<Basket(id={self.id}, token='{self.basket_token}', customer_id={self.customer_id})>"
    
    @property
    def item_count(self) -> int:
        """获取商品总数"""
        return sum(item.quantity for item in self.items) if self.items else 0
    
    @property
    def unique_item_count(self) -> int:
        """获取唯一商品数"""
        return len(self.items) if self.items else 0
    
    @property
    def is_empty(self) -> bool:
        """购物车是否为空"""
        return self.item_count == 0
    
    @property
    def is_expired(self) -> bool:
        """购物车是否已过期"""
        if not self.expires_at:
            return False
        from datetime import datetime
        return datetime.utcnow() > self.expires_at
    
    @property
    def formatted_total(self) -> str:
        """格式化总金额"""
        return f"{self.currency} {self.total_amount:.2f}"
    
    def calculate_totals(self):
        """计算购物车总金额"""
        if not self.items:
            self.subtotal = 0
            self.total_amount = 0
            return
        
        # 计算商品小计
        self.subtotal = sum(
            item.unit_price * item.quantity for item in self.items
        )
        
        # 计算总计（商品小计 + 运费 + 税费 - 折扣）
        self.total_amount = (
            self.subtotal + 
            self.shipping_amount + 
            self.tax_amount - 
            self.discount_amount
        )
    
    def add_item(self, product_id: int, quantity: int, unit_price: float, variant_id: int = None, **kwargs):
        """添加商品到购物车"""
        from .basket_item import BasketItem
        
        # 检查是否已存在相同商品
        existing_item = None
        for item in self.items:
            if item.product_id == product_id and item.variant_id == variant_id:
                existing_item = item
                break
        
        if existing_item:
            # 更新现有商品数量
            existing_item.quantity += quantity
            existing_item.updated_at = func.now()
        else:
            # 创建新商品项
            new_item = BasketItem(
                basket_id=self.id,
                product_id=product_id,
                variant_id=variant_id,
                quantity=quantity,
                unit_price=unit_price,
                **kwargs
            )
            self.items.append(new_item)
        
        # 重新计算总金额
        self.calculate_totals()
        self.last_activity_at = func.now()
    
    def remove_item(self, item_id: int):
        """从购物车移除商品"""
        item_to_remove = None
        for item in self.items:
            if item.id == item_id:
                item_to_remove = item
                break
        
        if item_to_remove:
            self.items.remove(item_to_remove)
            self.calculate_totals()
            self.last_activity_at = func.now()
            return True
        
        return False
    
    def clear(self):
        """清空购物车"""
        self.items.clear()
        self.calculate_totals()
        self.last_activity_at = func.now()
    
    def to_dict(self, include_items: bool = True, include_relations: bool = False) -> dict:
        """转换为字典"""
        result = {
            'id': self.id,
            'shop_id': self.shop_id,
            'customer_id': self.customer_id,
            'basket_token': self.basket_token,
            'session_id': self.session_id,
            'status': self.status,
            'is_guest': self.is_guest,
            'subtotal': float(self.subtotal) if self.subtotal else 0,
            'discount_amount': float(self.discount_amount) if self.discount_amount else 0,
            'shipping_amount': float(self.shipping_amount) if self.shipping_amount else 0,
            'tax_amount': float(self.tax_amount) if self.tax_amount else 0,
            'total_amount': float(self.total_amount) if self.total_amount else 0,
            'currency': self.currency,
            'coupon_code': self.coupon_code,
            'discount_rules': self.discount_rules or {},
            'shipping_method': self.shipping_method,
            'shipping_address_id': self.shipping_address_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_activity_at': self.last_activity_at.isoformat() if self.last_activity_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'basket_metadata': self.basket_metadata or {},  # 修改这里
            'notes': self.notes,
            'item_count': self.item_count,
            'unique_item_count': self.unique_item_count,
            'is_empty': self.is_empty,
            'is_expired': self.is_expired,
            'formatted_total': self.formatted_total
        }
        
        if include_items and self.items:
            result['items'] = [item.to_dict() for item in self.items]
        
        if include_relations:
            result['shop'] = {
                'id': self.shop.id,
                'name': self.shop.name
            } if self.shop else None
            
            result['customer'] = {
                'id': self.customer.id,
                'email': self.customer.email,
                'full_name': self.customer.full_name
            } if self.customer else None
            
            if self.shipping_address:
                result['shipping_address'] = self.shipping_address.to_dict()
        
        return result