# backend/app/models/user.py
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.database import Base


class User(Base):
    """Модель пользовательских данных"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    
    # Поле личной информации
    first_name = Column(String(50), nullable=True)  # Имя
    last_name = Column(String(50), nullable=True)   # Фамилия
    phone = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Поле состояния
    is_verified = Column(Boolean, default=False)  # Статус проверки почтового ящика
    is_active = Column(Boolean, default=True)
    is_profile_completed = Column(Boolean, default=False)  # Выполнение личных данных
    
    # Метка времени
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Отношения
    owned_shops = relationship("Shop", back_populates="owner", cascade="all, delete-orphan")
    shop_members = relationship("ShopMember", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
    
    @property
    def full_name(self):
        """Вернуться к полному имени"""
        if self.first_name and self.last_name:
            return f"{self.last_name} {self.first_name}"
        return self.email