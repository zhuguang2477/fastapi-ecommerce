import os
from sqlalchemy import create_engine, text
from backend.app.core.config import settings

def test_connection():
    try:
        print(f"Попытка подключения к базе данных: {settings.DATABASE_URL}")
        
        # Создать движок
        engine = create_engine(settings.DATABASE_URL)
        
        # Проверить соединение
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Успешное подключение PostgreSQL!")
            print(f"Версия PostgreSQL: {version}")
            
            # Список тестовых баз данных
            result = conn.execute(text("SELECT datname FROM pg_database WHERE datistemplate = false;"))
            databases = [row[0] for row in result]
            print(f"Доступные базы данных: {databases}")
            
            return True
            
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return False

if __name__ == "__main__":
    test_connection()
