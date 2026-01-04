# backend/app/models/recipient.py
"""
收货人模型
存储客户的收货人信息，支持多个收货地址
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.database import Base


class Recipient(Base):
    """Модель получателя (收货人)"""
    __tablename__ = "recipients"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    
    # 收货人基本信息
    recipient_name = Column(String(100), nullable=False)
    recipient_phone = Column(String(50), nullable=False)
    recipient_email = Column(String(255), nullable=True)
    
    # 地址信息
    country = Column(String(100), nullable=False, default="")
    province = Column(String(100), nullable=False, default="")
    city = Column(String(100), nullable=False, default="")
    district = Column(String(100), nullable=True)
    address_line1 = Column(String(500), nullable=False)
    address_line2 = Column(String(500), nullable=True)
    postal_code = Column(String(20), nullable=True)
    
    # 地址标签和类型
    address_label = Column(String(100), nullable=True)
    address_type = Column(String(50), nullable=False, default="shipping")
    
    # 附加信息
    is_default_shipping = Column(Boolean, default=False)
    is_default_billing = Column(Boolean, default=False)
    
    # 地理坐标 (可选)
    latitude = Column(String(50), nullable=True)
    longitude = Column(String(50), nullable=True)
    
    # 状态信息
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    
    # 验证信息
    is_verified = Column(Boolean, default=False)
    verification_date = Column(DateTime(timezone=True), nullable=True)
    
    # 审计字段
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    shop = relationship("Shop", back_populates="recipients")
    customer = relationship("Customer", back_populates="recipients")
    created_by_user = relationship("User", back_populates="created_recipients")
    orders = relationship("Order", back_populates="recipient", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('ix_recipients_customer_type', 'customer_id', 'address_type'),
        Index('ix_recipients_shop_customer', 'shop_id', 'customer_id'),
        Index('ix_recipients_full_address', 'country', 'province', 'city', 'district'),
    )
    
    def __repr__(self):
        return f"<Recipient(id={self.id}, name='{self.recipient_name}', customer_id={self.customer_id})>"
    
    @property
    def full_address(self) -> str:
        """获取完整地址字符串"""
        address_parts = []
        
        if self.country:
            address_parts.append(self.country)
        if self.province:
            address_parts.append(self.province)
        if self.city:
            address_parts.append(self.city)
        if self.district:
            address_parts.append(self.district)
        if self.address_line1:
            address_parts.append(self.address_line1)
        if self.address_line2:
            address_parts.append(self.address_line2)
        if self.postal_code:
            address_parts.append(f"邮编: {self.postal_code}")
        
        return " ".join(address_parts)
    
    @property
    def short_address(self) -> str:
        """获取简短地址字符串"""
        return f"{self.city}{self.district or ''}{self.address_line1}"
    
    @property
    def is_default_address(self) -> bool:
        """是否为默认地址"""
        if self.address_type == "shipping":
            return self.is_default_shipping
        elif self.address_type == "billing":
            return self.is_default_billing
        elif self.address_type == "both":
            return self.is_default_shipping and self.is_default_billing
        return False
    
    def to_dict(self, include_relations: bool = False) -> dict:
        """转换为字典"""
        result = {
            'id': self.id,
            'shop_id': self.shop_id,
            'customer_id': self.customer_id,
            'recipient_name': self.recipient_name,
            'recipient_phone': self.recipient_phone,
            'recipient_email': self.recipient_email,
            'country': self.country,
            'province': self.province,
            'city': self.city,
            'district': self.district,
            'address_line1': self.address_line1,
            'address_line2': self.address_line2,
            'postal_code': self.postal_code,
            'address_label': self.address_label,
            'address_type': self.address_type,
            'is_default_shipping': self.is_default_shipping,
            'is_default_billing': self.is_default_billing,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'verification_date': self.verification_date.isoformat() if self.verification_date else None,
            'notes': self.notes,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'full_address': self.full_address,
            'short_address': self.short_address,
            'is_default_address': self.is_default_address
        }
        
        if include_relations:
            result['customer'] = {
                'id': self.customer.id,
                'email': self.customer.email,
                'full_name': self.customer.full_name
            } if self.customer else None
            
            result['shop'] = {
                'id': self.shop.id,
                'name': self.shop.name
            } if self.shop else None
            
            result['created_by_user'] = {
                'id': self.created_by_user.id,
                'email': self.created_by_user.email
            } if self.created_by_user else None
            
            result['orders_count'] = len(self.orders) if self.orders else 0
        
        return result