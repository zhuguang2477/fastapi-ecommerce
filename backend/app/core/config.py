import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Конфигурация проекта
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "FastAPI Ecommerce Platform")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    
    # Настройка базы данных - построение URL - адресов из независимых параметров
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "ecommerce_db")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    
    # Создать полный URL базы данных
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Настройка Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: str = os.getenv("REDIS_PORT", "6379")
    
    # Создание полного URL - адреса Redis
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
    
    # Настройка JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key")
    
    # Настройка CORS
    ALLOWED_ORIGINS: List[str] = eval(os.getenv("ALLOWED_ORIGINS", '["http://localhost:3000"]'))

settings = Settings()