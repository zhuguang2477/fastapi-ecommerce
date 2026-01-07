# backend/app/models/otp.py
"""
OTP模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index
from datetime import datetime
from backend.app.database import Base


class OTP(Base):
    __tablename__ = "otps"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    otp_code = Column(String(6), nullable=False)
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    ip_address = Column(String(45), nullable=True)
    used_at = Column(DateTime, nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    purpose = Column(String(50), nullable=True, default="login")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<OTP(id={self.id}, email={self.email}, otp_code={self.otp_code[:3]}***)>"
    
    __table_args__ = (
        Index('idx_otp_email_created', 'email', 'created_at'),
    )