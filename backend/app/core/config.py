# backend/app/core/config.py
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional, List
import json

class Settings(BaseSettings):
    """Конфигурация приложения"""
    
    # Настройки приложения
    PROJECT_NAME: str = "FastAPI E-commerce платформа"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    
    # Конфигурация базы данных - использование полного DATABASE_URL
    DATABASE_URL: str = "postgresql://postgres:506767@localhost:5432/ecommerce_db"
    
    # Или использование отдельных настроек (если нужно)
    POSTGRES_SERVER: Optional[str] = "localhost"
    POSTGRES_USER: Optional[str] = "postgres"
    POSTGRES_PASSWORD: Optional[str] = "506767"
    POSTGRES_DB: Optional[str] = "ecommerce_db"
    POSTGRES_PORT: Optional[str] = "5432"
    
    # Конфигурация JWT
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Конфигурация Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: Optional[str] = "localhost"
    REDIS_PORT: Optional[int] = 6379
    
    # Конфигурация SMTP
    SMTP_SERVER: Optional[str] = "smtp.gmail.com"
    SMTP_PORT: Optional[int] = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SENDER_EMAIL: Optional[str] = "noreply@yourapp.com"
    
    # Настройки электронной почты
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SENDER_EMAIL: str = "noreply@yourapp.com"
    
    # Настройки шаблонов писем
    EMAIL_VERIFICATION_SUBJECT: str = "Ваш код подтверждения - {app_name}"
    EMAIL_WELCOME_SUBJECT: str = "Добро пожаловать в {app_name}!"
    
    # Название приложения
    APP_NAME: str = "FastAPI E-commerce платформа"

    # Настройки окружения
    ENVIRONMENT: str = "development"
    
    # Конфигурация CORS - использование списка строк
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Настройки загрузки файлов
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: List[str] = ["jpg", "jpeg", "png", "gif"]
    
    # Настройки приложения
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    
    class Config:
        env_file = ".env"
        # Разрешить дополнительные поля, чтобы избежать ошибок валидации
        extra = "ignore"

# Создание экземпляра конфигурации
settings = Settings()

# Вывод информации о конфигурации (для отладки)
print(f"✅ Конфигурация успешно загружена:")
print(f"   Окружение: {settings.ENVIRONMENT}")
print(f"   База данных: {settings.DATABASE_URL}")
print(f"   Redis: {settings.REDIS_URL}")
print(f"   CORS Origins: {settings.BACKEND_CORS_ORIGINS}")