# backend/app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger(__name__)

# Импорт из конфигурации
try:
    from backend.app.core.config import settings
    
    # Создание движка базы данных
    SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
    
    logger.info(f"Подключение к базе данных: {SQLALCHEMY_DATABASE_URL[:40]}...")
    
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,  # Проверка соединения перед использованием
        echo=settings.DEBUG   # Показывать SQL в режиме отладки
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Создание декларативного базового класса - это ключевой элемент
    Base = declarative_base()
    
    logger.info("✅ Конфигурация базы данных успешно завершена")
    
except Exception as e:
    logger.error(f"❌ Ошибка конфигурации базы данных: {e}")
    # Создание значений по умолчанию для предотвращения полного краха приложения
    engine = None
    SessionLocal = None
    Base = declarative_base()  # Создаем Base даже при ошибке конфигурации

def get_db():
    """Получение сессии базы данных"""
    if SessionLocal is None:
        raise RuntimeError("База данных не настроена правильно")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()