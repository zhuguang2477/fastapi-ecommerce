from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path

from backend.app.core.config import settings
from backend.app.core.email import email_service, send_email
from backend.app.api.v1.api import api_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Получение корневой директории проекта
PROJECT_ROOT = Path(__file__).parent.parent.parent
UPLOAD_DIR = PROJECT_ROOT / "uploads"

# Обеспечение существования директорий для загрузок
def ensure_upload_dirs():
    """Обеспечить существование директорий для загрузок"""
    logger.info(f"📂 Корневая директория проекта: {PROJECT_ROOT}")
    logger.info(f"📁 Директория загрузок: {UPLOAD_DIR}")
    
    directories = [
        UPLOAD_DIR,
        UPLOAD_DIR / "products",
        UPLOAD_DIR / "shops",
        UPLOAD_DIR / "temp"
    ]
    
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Создана директория: {directory}")
        except Exception as e:
            logger.error(f"❌ Не удалось создать директорию {directory}: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Действия при запуске
    logger.info("🚀 Запуск FastAPI e-commerce платформы...")
    
    # Обеспечение существования директорий для загрузок
    ensure_upload_dirs()
    
    # Тест загрузки конфигурации
    try:
        from backend.app.core.config import settings
        logger.info("✅ Конфигурация успешно загружена:")
        logger.info(f"   Окружение: {settings.ENVIRONMENT}")
        
        # Безопасное отображение URL базы данных (скрыть пароль)
        if hasattr(settings, 'DATABASE_URL'):
            db_url = settings.DATABASE_URL
            # Скрыть пароль
            if '@' in db_url:
                parts = db_url.split('@')
                if '://' in parts[0]:
                    protocol_user = parts[0].split('://')
                    if len(protocol_user) == 2:
                        protocol, user_pass = protocol_user
                        if ':' in user_pass:
                            user, _ = user_pass.split(':', 1)
                            db_url = f"{protocol}://{user}:****@{parts[1]}"
            logger.info(f"   База данных: {db_url}")
        else:
            logger.warning("⚠️  Не найдена конфигурация DATABASE_URL")
        
        if hasattr(settings, 'REDIS_URL'):
            logger.info(f"   Redis: {settings.REDIS_URL}")
        else:
            logger.warning("⚠️  Не найдена конфигурация REDIS_URL")
            
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки конфигурации: {e}")
    
    # Тест почтового сервиса
    await test_email_service()
    
    yield  # Приложение работает
    
    # Действия при остановке
    logger.info("🛑 Остановка приложения...")

async def test_email_service():
    """Тестирование почтового сервиса"""
    try:
        logger.info("📧 Начало тестирования почтового сервиса...")
        
        # Получение имени приложения
        app_name = getattr(settings, 'APP_NAME', 'FastAPI e-commerce платформа')
        
        # Создание тестового содержимого письма
        subject = f"Тест почтового сервиса - {app_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body>
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                <h2 style="color: #4CAF50;">Тест почтового сервиса</h2>
                <p>Это тестовое письмо от <strong>{app_name}</strong>.</p>
                <p>Если вы получили это письмо, значит почтовый сервис настроен правильно!</p>
                <p>Текущий режим: <strong>{'Симуляция' if email_service.simulation_mode else 'Реальный режим отправки'}</strong></p>
                <hr>
                <p style="color: #777; font-size: 12px;">
                    Время тестирования: 2025-12-15 18:00:00
                </p>
            </div>
        </body>
        </html>
        """
        
        # Отправка тестового письма (используем тестового получателя)
        success = await send_email(
            email_to="test@example.com",
            subject=subject,
            html_content=html_content
        )
        
        if success:
            if email_service.simulation_mode:
                logger.info("✅ Тест почтового сервиса успешен (режим симуляции)")
                logger.info("ℹ️  Письмо не было отправлено фактически, но в продакшн среде будет отправлено")
            else:
                logger.info("✅ Тест почтового сервиса успешен (режим реальной отправки)")
                logger.info("📤 Тестовое письмо отправлено на test@example.com")
        else:
            logger.warning("⚠️  Тест почтового сервиса не удался")
            
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования почтового сервиса: {e}")

# Создание FastAPI приложения
app = FastAPI(
    title="FastAPI e-commerce платформа",
    version="1.0.0",
    description="Backend API для e-commerce платформы",
    lifespan=lifespan
)

# Добавление CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтирование директории статических файлов
try:
    if os.path.exists("uploads"):
        app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
        logger.info("✅ Директория статических файлов успешно смонтирована: /uploads")
    else:
        logger.warning("⚠️  Директория загрузок не существует, пропускаем монтирование статических файлов")
except Exception as e:
    logger.error(f"❌ Ошибка монтирования директории статических файлов: {e}")

@app.get("/")
async def root():
    """Корневая конечная точка"""
    return {
        "message": "Добро пожаловать в FastAPI e-commerce платформу",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "environment": settings.ENVIRONMENT,
        "mail_service": "Режим симуляции" if email_service.simulation_mode else "Режим реальной отправки"
    }

@app.get("/health")
async def health_check():
    """Проверка работоспособности"""
    from datetime import datetime
    return {
        "status": "healthy",
        "service": "fastapi-ecommerce",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "environment": settings.ENVIRONMENT,
        "mail_service": {
            "mode": "simulation" if email_service.simulation_mode else "real",
            "smtp_server": email_service.smtp_host if not email_service.simulation_mode else "Режим симуляции",
            "status": "operational"
        }
    }

# Импорт и подключение API роутов
try:
    from backend.app.api.v1.api import api_router
    
    # Получение префикса API
    api_prefix = getattr(settings, 'API_V1_STR', '/api/v1')
    app.include_router(api_router, prefix=api_prefix)
    logger.info(f"✅ API роуты успешно загружены, префикс: {api_prefix}")
    
except ImportError as e:
    logger.error(f"❌ Ошибка импорта API роутов: {e}")
    
    # Создание базовых роутов как запасной вариант
    from fastapi import APIRouter
    
    fallback_router = APIRouter()
    
    @fallback_router.get("/health")
    async def fallback_health():
        return {"status": "healthy", "message": "Используются запасные роуты"}
    
    app.include_router(fallback_router, prefix="/api/v1")
    logger.warning("⚠️  Используются запасные API роуты")

# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Логирование HTTP запросов"""
    # Пропуск детального логгирования для статических файлов и проверки работоспособности
    skip_paths = ["/health", "/favicon.ico", "/static/", "/uploads/"]
    
    if not any(request.url.path.startswith(path) for path in skip_paths):
        logger.info(f"🌐 {request.method} {request.url.path}")
    
    response = await call_next(request)
    return response

# Глобальная обработка исключений
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Глобальная обработка исключений"""
    logger.error(f"🚨 Необработанное исключение: {exc}")
    
    # Проверка режима отладки
    debug_mode = getattr(settings, 'DEBUG', False)
    
    return {
        "error": "Внутренняя ошибка сервера",
        "detail": str(exc) if debug_mode else "Пожалуйста, попробуйте позже"
    }