from backend.app.database import engine
from backend.app.models.base import Base

def init_db():
    try:
        # Создать все таблицы
        Base.metadata.create_all(bind=engine)
        print("✅ Таблица базы данных создана успешно!")
        
        # Проверить созданные таблицы
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Создать таблицу: {tables}")
        
    except Exception as e:
        print(f"❌ Ошибка создания таблицы базы данных: {e}")

if __name__ == "__main__":
    init_db()
