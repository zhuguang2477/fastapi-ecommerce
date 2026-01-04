# backend/app/models/basket_item.py
"""
购物车商品项模型
代表购物车中的单个商品
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, Numeric, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.database import Base


class BasketItem(Base):
    """Модель товара в корзине (购物车商品项)"""
    __tablename__ = "basket_items"
    
    id = Column(Integer, primary_key=True, index=True)
    basket_id = Column(Integer, ForeignKey("baskets.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    # 商品变体信息
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=True, index=True)
    
    # 商品信息快照 (在加入购物车时保存)
    product_name = Column(String(200), nullable=False)
    product_sku = Column(String(100), nullable=True)
    variant_name = Column(String(200), nullable=True)
    variant_attributes = Column(JSON, nullable=True)
    
    # 价格信息
    unit_price = Column(Numeric(10, 2), nullable=False)
    original_price = Column(Numeric(10, 2), nullable=True)
    discount_amount = Column(Numeric(10, 2), default=0)
    
    # 数量信息
    quantity = Column(Integer, nullable=False, default=1)
    max_quantity = Column(Integer, nullable=True)
    
    # 商品信息
    product_image_url = Column(String(500), nullable=True)
    product_slug = Column(String(200), nullable=True)
    
    # 库存信息
    is_in_stock = Column(Boolean, default=True)
    stock_quantity = Column(Integer, nullable=True)
    
    # 配送信息
    requires_shipping = Column(Boolean, default=True)
    weight = Column(Numeric(10, 2), nullable=True)
    dimensions = Column(JSON, nullable=True)
    
    # 折扣信息
    discount_percentage = Column(Numeric(5, 2), default=0)
    discount_reason = Column(String(200), nullable=True)
    
    # 时间信息
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 元数据 - 修改字段名避免冲突
    item_metadata = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    
    # 关系
    basket = relationship("Basket", back_populates="items")
    product = relationship("Product")
    variant = relationship("ProductVariant")
    
    # 索引
    __table_args__ = (
        Index('ix_basket_items_basket_product', 'basket_id', 'product_id', 'variant_id', unique=True),
        Index('ix_basket_items_added_at', 'added_at'),
    )
    
    def __repr__(self):
        return f"<BasketItem(id={self.id}, product='{self.product_name}', quantity={self.quantity})>"
    
    @property
    def line_total(self) -> float:
        """获取商品行总计"""
        return float((self.unit_price - self.discount_amount) * self.quantity)
    
    @property
    def formatted_unit_price(self) -> str:
        """格式化单价"""
        basket = self.basket
        currency = basket.currency if basket else "CNY"
        return f"{currency} {self.unit_price:.2f}"
    
    @property
    def formatted_line_total(self) -> str:
        """格式化行总计"""
        basket = self.basket
        currency = basket.currency if basket else "CNY"
        return f"{currency} {self.line_total:.2f}"
    
    @property
    def discount_percentage_display(self) -> float:
        """获取显示的折扣百分比"""
        if self.original_price and self.original_price > 0:
            discount = ((self.original_price - self.unit_price) / self.original_price) * 100
            return round(discount, 2)
        return 0.0
    
    @property
    def display_name(self) -> str:
        """获取显示名称"""
        if self.variant_name:
            return f"{self.product_name} - {self.variant_name}"
        return self.product_name
    
    @property
    def is_discounted(self) -> bool:
        """是否享受折扣"""
        return self.discount_amount > 0 or self.discount_percentage > 0
    
    @property
    def can_increase_quantity(self) -> bool:
        """是否可以增加数量"""
        if self.max_quantity:
            return self.quantity < self.max_quantity
        return True
    
    def update_quantity(self, new_quantity: int) -> bool:
        """更新商品数量"""
        if new_quantity <= 0:
            return False
        
        if self.max_quantity and new_quantity > self.max_quantity:
            return False
        
        self.quantity = new_quantity
        self.updated_at = func.now()
        return True
    
    def increase_quantity(self, amount: int = 1) -> bool:
        """增加商品数量"""
        return self.update_quantity(self.quantity + amount)
    
    def decrease_quantity(self, amount: int = 1) -> bool:
        """减少商品数量"""
        if self.quantity - amount <= 0:
            return False
        return self.update_quantity(self.quantity - amount)
    
    def apply_discount(self, discount_amount: float = None, discount_percentage: float = None, reason: str = None):
        """应用折扣"""
        if discount_amount is not None:
            self.discount_amount = discount_amount
        elif discount_percentage is not None:
            if self.unit_price > 0:
                self.discount_amount = self.unit_price * (discount_percentage / 100)
        
        if reason:
            self.discount_reason = reason
        
        self.updated_at = func.now()
    
    def to_dict(self, include_relations: bool = False) -> dict:
        """转换为字典"""
        result = {
            'id': self.id,
            'basket_id': self.basket_id,
            'product_id': self.product_id,
            'variant_id': self.variant_id,
            'product_name': self.product_name,
            'product_sku': self.product_sku,
            'variant_name': self.variant_name,
            'variant_attributes': self.variant_attributes or {},
            'unit_price': float(self.unit_price) if self.unit_price else 0,
            'original_price': float(self.original_price) if self.original_price else 0,
            'discount_amount': float(self.discount_amount) if self.discount_amount else 0,
            'quantity': self.quantity,
            'max_quantity': self.max_quantity,
            'product_image_url': self.product_image_url,
            'product_slug': self.product_slug,
            'is_in_stock': self.is_in_stock,
            'stock_quantity': self.stock_quantity,
            'requires_shipping': self.requires_shipping,
            'weight': float(self.weight) if self.weight else None,
            'dimensions': self.dimensions or {},
            'discount_percentage': float(self.discount_percentage) if self.discount_percentage else 0,
            'discount_reason': self.discount_reason,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'item_metadata': self.item_metadata or {},  # 修改这里
            'notes': self.notes,
            'line_total': self.line_total,
            'formatted_unit_price': self.formatted_unit_price,
            'formatted_line_total': self.formatted_line_total,
            'discount_percentage_display': self.discount_percentage_display,
            'display_name': self.display_name,
            'is_discounted': self.is_discounted,
            'can_increase_quantity': self.can_increase_quantity
        }
        
        if include_relations:
            result['product'] = {
                'id': self.product.id,
                'name': self.product.name,
                'slug': self.product.slug,
                'status': self.product.status
            } if self.product else None
            
            if self.variant:
                result['variant'] = {
                    'id': self.variant.id,
                    'name': self.variant.name,
                    'sku': self.variant.sku
                }
        
        return result