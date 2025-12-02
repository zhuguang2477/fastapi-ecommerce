from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from backend.app.database import Base


class OTP(Base):
    """Одноразовая модель пароля"""
    __tablename__ = "otps"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    otp_code = Column(String(6), nullable=False)  # 6 - битный цифровой код проверки
    is_used = Column(Boolean, default=False)
    
    # Контроль срока действия
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    def __repr__(self):
        return f"<OTP(id={self.id}, email='{self.email}', otp_code='{self.otp_code}')>"