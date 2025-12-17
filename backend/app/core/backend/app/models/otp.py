# backend/app/models/otp.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.database import Base

class OTP(Base):
    """Модель одноразового пароля"""
    __tablename__ = "otps"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), ForeignKey('users.email'), nullable=False, index=True)
    otp_code = Column(String(6), nullable=False)  # 6-значный проверочный код
    is_used = Column(Boolean, default=False)
    
    # Контроль срока действия
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Связи
    user = relationship("User", back_populates="otps", foreign_keys=[email])
    
    def __repr__(self):
        return f"<OTP(id={self.id}, email='{self.email}', otp_code='{self.otp_code}')>"