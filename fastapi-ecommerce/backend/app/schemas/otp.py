# backend/app/schemas/otp.py
from pydantic import BaseModel
from typing import Optional
from .user import UserResponse

class OTPRequest(BaseModel):
    """Запрос OTP"""
    email: str

class OTPVerify(BaseModel):
    """Верификация OTP"""
    email: str
    otp_code: str

class TokenResponse(BaseModel):
    """Ответ с токеном"""
    access_token: str
    token_type: str = "bearer"
    user: Optional[UserResponse] = None
    user_id: Optional[int] = None
    email: Optional[str] = None
    is_profile_completed: Optional[bool] = None