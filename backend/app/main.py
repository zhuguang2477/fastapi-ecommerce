# backend/app/main.py
"""
Основное приложение FastAPI
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
import uvicorn
from datetime import datetime

from backend.app.core.config import settings
from backend.app.database import init_db, get_db
from backend.app.api.v1.api import api_router
from backend.app.core.security import security

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Бэкенд API платформы электронной коммерции FastAPI",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Настройка CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.on_event("startup")
async def startup_event():
    """Событие запуска"""
    logger.info("Запуск приложения FastAPI...")
    
    # Инициализация базы данных
    try:
        init_db()
        logger.info("Инициализация базы данных завершена")
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        raise
    
    # Проверка ключевых конфигураций
    if settings.SMTP_PASSWORD in ['your-app-password', 'test123', '']:
        logger.warning("⚠️ Конфигурация почты неполная, будет использоваться имитационный режим")
    else:
        logger.info("✅ Конфигурация почты полная, будут отправляться реальные письма")


@app.on_event("shutdown")
async def shutdown_event():
    """Событие завершения работы"""
    logger.info("Завершение работы приложения FastAPI...")


@app.get("/")
async def root():
    """Корневой путь"""
    return {
        "message": f"Добро пожаловать в API {settings.APP_NAME}",
        "version": "1.0.0",
        "docs": "/api/docs",
        "status": "работает"
    }


@app.get("/health")
async def health_check():
    """Проверка работоспособности"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/info")
async def api_info():
    """Информация об API"""
    return {
        "app_name": settings.APP_NAME,
        "version": "1.0.0",
        "api_version": "v1",
        "docs_url": "/api/docs",
        "auth_method": "OTP",
        "features": [
            "OTP аутентификация по электронной почте",
            "JWT токены",
            "Управление профилями пользователей",
            "Отправка писем через Gmail"
        ]
    }


# Подключение API маршрутов
app.include_router(api_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )