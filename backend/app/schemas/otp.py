# backend/app/schemas/otp.py
"""
OTP相关模式
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class OTPRequest(BaseModel):
    """OTP请求模型"""
    email: EmailStr
    purpose: str
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "purpose": "login"
            }
        }


class OTPVerify(BaseModel):
    """OTP验证模型"""
    email: EmailStr
    otp_code: str
    token: Optional[str] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "otp_code": "123456"
            }
        }


class OTPStatusResponse(BaseModel):
    """OTP状态响应"""
    email: EmailStr
    is_verified: bool
    otp_enabled: bool
    otp_verified: bool
    verification_expires_at: Optional[datetime] = None
    last_otp_sent_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    token_type: str = "bearer"
    user: dict 
    user_id: int
    email: EmailStr
    is_profile_completed: bool
    otp_status: OTPStatusResponse
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "first_name": "张",
                    "last_name": "三",
                    "phone": "+8613812345678",
                    "is_verified": True,
                    "is_active": True,
                    "is_profile_completed": True,
                    "otp_enabled": True,
                    "otp_verified": True,
                    "avatar_url": "https://example.com/avatar.jpg",
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00"
                },
                "user_id": 1,
                "email": "user@example.com",
                "is_profile_completed": True,
                "otp_status": {
                    "email": "user@example.com",
                    "is_verified": True,
                    "otp_enabled": True,
                    "otp_verified": True,
                    "verification_expires_at": "2024-01-01T00:10:00",
                    "last_otp_sent_at": "2024-01-01T00:00:00"
                }
            }
        }