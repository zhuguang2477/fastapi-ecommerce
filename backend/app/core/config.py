# backend/app/core/config.py
from typing import List, Optional, Union, Dict, Any
from pydantic import Field, validator
from pydantic_settings import BaseSettings
import secrets
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    # 项目配置
    PROJECT_NAME: str = "FastAPI Платформа электронной коммерции"
    APP_NAME: str = Field(default="FastAPI Платформа электронной коммерции")
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # 安全配置
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    # 数据库配置 - 移除默认值，强制从.env文件读取
    DATABASE_URL: str = Field(...)
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    # 邮件配置
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # 文件上传配置
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]
    
    # 缓存配置
    CACHE_TTL: int = 300
    
    # 验证码配置
    OTP_EXPIRE_MINUTES: int = 10
    OTP_LENGTH: int = 6
    
    # 店铺配置
    DEFAULT_SHOP_PASSWORD_LENGTH: int = 8
    MAX_SHOP_MEMBERS: int = 10
    
    # 模型配置 - 修正.env文件路径
    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "case_sensitive": False
    }
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v: str) -> str:
        if not v:
            raise ValueError("DATABASE_URL не может быть пустым")
        return v
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("Длина SECRET_KEY должна быть не менее 32 символов")
        return v


try:
    settings = Settings()
except Exception as e:
    print(f"❌ 配置文件加载失败: {e}")
    print(f"请确保存在 .env 文件，并且包含必要的配置项")
    print(f"配置文件路径: {BASE_DIR / '.env'}")
    print(f"必需的配置项: DATABASE_URL, SECRET_KEY")
    raise

# 提供向后兼容的别名
class Config:
    """Класс конфигурации для обратной совместимости"""
    def __init__(self):
        self.settings = settings
    
    def __getattr__(self, name):
        return getattr(self.settings, name)

config = Config()
