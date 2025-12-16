# backend/app/models/user.py
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.database import Base

class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    
    # Личная информация
    first_name = Column(String(50), nullable=True)  # Имя
    last_name = Column(String(50), nullable=True)   # Фамилия
    phone = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Статусы
    is_verified = Column(Boolean, default=False)  # Статус верификации email
    is_active = Column(Boolean, default=True)
    is_profile_completed = Column(Boolean, default=False)  # Статус заполнения профиля
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Отношения
    # Магазины, владельцем которых является пользователь
    owned_shops = relationship("Shop", back_populates="owner", foreign_keys="Shop.owner_id")
    
    # Магазины, в которых пользователь является участником
    shop_memberships = relationship("ShopMember", back_populates="user")
    
    # Заказы, созданные пользователем (как клиентом)
    orders_as_customer = relationship("Order", backref="customer_user", foreign_keys="Order.customer_email", primaryjoin="User.email==Order.customer_email")
    
    # OTP коды подтверждения
    otps = relationship("OTP", back_populates="user", foreign_keys="OTP.email", primaryjoin="User.email==OTP.email")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
    
    @property
    def full_name(self) -> str:
        """Получить полное имя пользователя"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.email.split('@')[0]
    
    @property
    def display_name(self) -> str:
        """Получить отображаемое имя (для UI)"""
        return self.full_name
    
    def update_profile(self, first_name: str = None, last_name: str = None, 
                      phone: str = None, avatar_url: str = None) -> None:
        """Обновить личную информацию пользователя"""
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
        if phone is not None:
            self.phone = phone
        if avatar_url is not None:
            self.avatar_url = avatar_url
        
        # Проверить полноту профиля
        self.check_profile_completion()
    
    def check_profile_completion(self) -> bool:
        """Проверить полноту личной информации"""
        # Основная информация: имя и телефон
        has_basic_info = bool(self.first_name and self.last_name and self.phone)
        
        # Обновить статус заполнения
        self.is_profile_completed = has_basic_info
        
        return self.is_profile_completed
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь"""
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone,
            'avatar_url': self.avatar_url,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'is_profile_completed': self.is_profile_completed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_initial(self) -> str:
        """Получить первую букву имени пользователя (для отображения аватара)"""
        if self.first_name:
            return self.first_name[0].upper()
        elif self.last_name:
            return self.last_name[0].upper()
        else:
            return self.email[0].upper()