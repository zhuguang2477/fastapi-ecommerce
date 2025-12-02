# backend/app/schemas/auth.py
from pydantic import BaseModel, EmailStr, ConfigDict


class SendOTPRequest(BaseModel):
    """Отправить запрос OTP"""
    email: EmailStr
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com"
            }
        }
    )


class ConfirmOTPRequest(BaseModel):
    """Подтвердить запрос OTP"""
    email: EmailStr
    otp: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "otp": "123456"
            }
        }
    )