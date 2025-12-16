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
    join_password = Column(String(100), nullable=False)           # Пароль для вступления
    is_active = Column(Boolean, default=True)                     # Активен ли
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Связи
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    owner = relationship("User", back_populates="owned_shops", foreign_keys=[owner_id])
    
    # Участники
    members = relationship("ShopMember", back_populates="shop", cascade="all, delete-orphan")
    
    # Категории
    categories = relationship("Category", back_populates="shop", cascade="all, delete-orphan")
    
    # Товары
    products = relationship("Product", back_populates="shop", cascade="all, delete-orphan")
    
    # Заказы
    orders = relationship("Order", back_populates="shop", cascade="all, delete-orphan")
    
    # Клиенты
    customers = relationship("Customer", back_populates="shop", cascade="all, delete-orphan")
    
    # Настройки
    settings = relationship("ShopSettings", back_populates="shop", uselist=False, cascade="all, delete-orphan")
    
    # Дизайн
    design = relationship("ShopDesign", back_populates="shop", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Shop(id={self.id}, name='{self.name}')>"


class ShopMember(Base):
    """Модель участника магазина"""
    __tablename__ = "shop_members"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey('shops.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_admin = Column(Boolean, default=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    shop = relationship("Shop", back_populates="members")
    user = relationship("User", back_populates="shop_memberships")
    
    def __repr__(self):
        return f"<ShopMember(shop_id={self.shop_id}, user_id={self.user_id}, is_admin={self.is_admin})>"