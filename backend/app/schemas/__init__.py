# backend/app/schemas/__init__.py

# Schemas package
from backend.app.schemas.health import HealthCheckResponse, DatabaseHealthResponse, RedisHealthResponse
from backend.app.schemas.user import (
    UserBase,
    UserCreate,
    UserResponse,
    UserUpdate,
    Token,
    TokenData
)
from backend.app.schemas.otp import OTPRequest, OTPVerify, TokenResponse
from backend.app.schemas.auth import SendOTPRequest, ConfirmOTPRequest
from backend.app.schemas.profile import ProfileUpdate, ProfileResponse
from backend.app.schemas.shop import ShopCreate, ShopJoinRequest, ShopResponse, ShopMemberResponse

__all__ = [
    "HealthCheckResponse",
    "DatabaseHealthResponse", 
    "RedisHealthResponse",
    "UserBase",
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    "Token",
    "TokenData",
    "OTPRequest",
    "OTPVerify",
    "TokenResponse",
    "SendOTPRequest",
    "ConfirmOTPRequest",
    "ProfileUpdate",
    "ProfileResponse",
    "ShopCreate",
    "ShopJoinRequest",
    "ShopResponse",
    "ShopMemberResponse"
]