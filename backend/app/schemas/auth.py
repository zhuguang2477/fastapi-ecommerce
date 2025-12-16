# backend/app/schemas/auth.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class SendOTPRequest(BaseModel):
    """Запрос на отправку OTP"""
    email: EmailStr = Field(..., description="Электронная почта пользователя")
    
class ConfirmOTPRequest(BaseModel):
    """Запрос на подтверждение OTP"""
    email: EmailStr = Field(..., description="Электронная почта пользователя")
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-значный проверочный код")

class RegisterRequest(BaseModel):
    """Запрос на регистрацию"""
    email: EmailStr = Field(..., description="Электронная почта пользователя")
    password: str = Field(..., min_length=8, max_length=128, description="Пароль")
    first_name: Optional[str] = Field(None, max_length=50, description="Имя")
    last_name: Optional[str] = Field(None, max_length=50, description="Фамилия")