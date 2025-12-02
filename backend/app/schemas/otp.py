# backend/app/schemas/otp.py
from pydantic import BaseModel, EmailStr, ConfigDict


class OTPRequest(BaseModel):
    """Модель запроса OTP"""
    email: EmailStr

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com"
            }
        }
    )


class OTPVerify(BaseModel):
    """Модель проверки OTP"""
    email: EmailStr
    otp_code: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "otp_code": "123456"
            }
        }
    )


class TokenResponse(BaseModel):
    """Модель токена"""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    is_profile_completed: bool

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "user_id": 1,
                "email": "user@example.com",
                "is_profile_completed": True
            }
        }
    )