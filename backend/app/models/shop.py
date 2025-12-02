# backend/app/models/shop.py
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.database import Base


class Shop(Base):
    """Модель магазина"""
    __tablename__ = "shops"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)                    # Название магазина
    description = Column(Text, nullable=True)                     # Описание магазина
    join_password = Column(String(100), nullable=False)           # Добавить пароль
    is_active = Column(Boolean, default=True)                     # Активны ли
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Отношения
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    owner = relationship("User", back_populates="owned_shops")
    
    # Членство
    members = relationship("ShopMember", back_populates="shop", cascade="all, delete-orphan")


class ShopMember(Base):
    """Модель для членов магазина"""
    __tablename__ = "shop_members"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey('shops.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Роль прав
    role = Column(String(50), default='viewer')  # 'owner', 'admin', 'editor', 'viewer'
    is_approved = Column(Boolean, default=False)  # Ратифицировано ли присоединение
    
    # Метка времени
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Отношения
    shop = relationship("Shop", back_populates="members")
    user = relationship("User", back_populates="shop_members")