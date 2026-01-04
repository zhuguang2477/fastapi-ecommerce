# backend/app/models/shop.py
"""
店铺模型
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.database import Base


class Shop(Base):
    """Модель магазина"""
    __tablename__ = "shops"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    join_password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系 - 添加新的关系
    owner = relationship(
        "User", 
        back_populates="owned_shops",
        foreign_keys=[owner_id]
    )
    members = relationship(
        "ShopMember",
        back_populates="shop",
        foreign_keys="ShopMember.shop_id",
        cascade="all, delete-orphan"
    )
    products = relationship("Product", back_populates="shop", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="shop", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="shop", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="shop", cascade="all, delete-orphan")
    
    # 新增关系
    settings = relationship("ShopSettings", back_populates="shop", uselist=False, cascade="all, delete-orphan")
    design = relationship("ShopDesign", back_populates="shop", uselist=False, cascade="all, delete-orphan")
    recipients = relationship("Recipient", back_populates="shop", cascade="all, delete-orphan")
    baskets = relationship("Basket", back_populates="shop", cascade="all, delete-orphan")
    
    # 分析关系
    analytics_reports = relationship("AnalyticsReport", back_populates="shop", cascade="all, delete-orphan")
    daily_analytics = relationship("DailyAnalytics", back_populates="shop", cascade="all, delete-orphan")
    product_analytics = relationship("ProductAnalytics", back_populates="shop", cascade="all, delete-orphan")
    traffic_sources = relationship("TrafficSource", back_populates="shop", cascade="all, delete-orphan")

    hero_banners = relationship("HeroBanner", back_populates="shop", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Shop(id={self.id}, name='{self.name}', owner_id={self.owner_id})>"
    
    @property
    def total_products(self) -> int:
        """获取店铺商品总数"""
        return len(self.products) if self.products else 0
    
    @property
    def total_orders(self) -> int:
        """获取店铺订单总数"""
        return len(self.orders) if self.orders else 0
    
    @property
    def total_customers(self) -> int:
        """获取店铺客户总数"""
        return len(self.customers) if self.customers else 0
    
    @property
    def total_members(self) -> int:
        """获取店铺成员总数"""
        return len(self.members) if self.members else 0
    
    def is_owner(self, user_id: int) -> bool:
        """检查用户是否是店铺所有者"""
        return self.owner_id == user_id
    
    def is_member(self, user_id: int) -> bool:
        """检查用户是否是店铺成员"""
        for member in self.members:
            if member.user_id == user_id and member.is_approved:
                return True
        return False
    
    def is_admin(self, user_id: int) -> bool:
        """检查用户是否是店铺管理员"""
        if self.is_owner(user_id):
            return True
        
        for member in self.members:
            if member.user_id == user_id and member.is_approved and member.is_admin:
                return True
        return False
    
    def to_dict(self, include_relations: bool = False) -> dict:
        """转换为字典"""
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'owner_id': self.owner_id,
            'total_products': self.total_products,
            'total_orders': self.total_orders,
            'total_customers': self.total_customers,
            'total_members': self.total_members
        }
        
        if include_relations:
            result['owner'] = {
                'id': self.owner.id,
                'email': self.owner.email,
                'full_name': f"{self.owner.first_name or ''} {self.owner.last_name or ''}".strip()
            } if self.owner else None
            
            if self.settings:
                result['settings'] = self.settings.to_dict()
            
            if self.design:
                result['design'] = self.design.to_dict()
        
        return result


class ShopMember(Base):
    """Модель участника магазина"""
    __tablename__ = "shop_members"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_admin = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    
    # 新增字段
    role = Column(String(50), default="viewer")
    permissions = Column(Text, nullable=True) 
    
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    shop = relationship("Shop", back_populates="members")
    user = relationship("User", back_populates="shop_memberships")
    
    def __repr__(self):
        return f"<ShopMember(id={self.id}, shop_id={self.shop_id}, user_id={self.user_id})>"
    
    def has_permission(self, permission: str) -> bool:
        """检查成员是否有特定权限"""
        if self.is_admin:
            return True
        
        if not self.permissions:
            return False
        
        import json
        try:
            permissions_list = json.loads(self.permissions)
            return permission in permissions_list
        except:
            return False
    
    def to_dict(self, include_relations: bool = False) -> dict:
        """转换为字典"""
        result = {
            'id': self.id,
            'shop_id': self.shop_id,
            'user_id': self.user_id,
            'is_admin': self.is_admin,
            'is_approved': self.is_approved,
            'role': self.role,
            'permissions': self.permissions,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None
        }
        
        if include_relations:
            result['shop'] = {
                'id': self.shop.id,
                'name': self.shop.name
            } if self.shop else None
            
            result['user'] = {
                'id': self.user.id,
                'email': self.user.email,
                'full_name': f"{self.user.first_name or ''} {self.user.last_name or ''}".strip()
            } if self.user else None
        
        return result