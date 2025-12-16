# backend/app/models/base.py
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.sql import func

# Примечание: здесь должен быть импорт Base из database
try:
    from backend.app.database import Base
except ImportError:
    # Если импорт не удался, создаем фиктивный Base
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()

class BaseModel(Base):
    """Базовый класс для всех моделей"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())