"""
用户模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # 认证状态
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_profile_completed = Column(Boolean, default=False)
    
    # OTP设置
    otp_enabled = Column(Boolean, default=False)
    otp_verified = Column(Boolean, default=False)
    
    # 个人资料
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    
    # 登录活动字段 - 添加这些字段
    login_count = Column(Integer, default=0)
    last_login_ip = Column(String(45), nullable=True)  # IPv4或IPv6
    registration_ip = Column(String(45), nullable=True)
    
    # 元数据
    preferences = Column(JSON, default={})  # 用户偏好设置
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    last_login_at = Column(DateTime, nullable=True)
    profile_completed_at = Column(DateTime, nullable=True)

    # 关系定义
    owned_shops = relationship(
        "Shop", 
        back_populates="owner",
        foreign_keys="Shop.owner_id",
        cascade="all, delete-orphan"
    )

    shop_memberships = relationship(
        "ShopMember",
        back_populates="user",
        foreign_keys="ShopMember.user_id",
        cascade="all, delete-orphan"
    )
    
    # 添加缺失的关系（与Recipient模型关联）
    created_recipients = relationship(
        "Recipient",
        back_populates="created_by_user",
        foreign_keys="Recipient.created_by",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
    
    @property
    def full_name(self) -> str:
        """获取用户全名"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.email.split('@')[0]
        
    @property
    def all_shops(self):
        owned = [shop for shop in self.owned_shops]
        member_shops = [member.shop for member in self.shop_memberships if member.shop]
        return owned + member_shops