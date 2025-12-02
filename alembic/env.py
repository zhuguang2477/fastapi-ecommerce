from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Добавить корневой каталог проекта в путь Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импорт конфигурации & base
from backend.app.core.config import settings
from backend.app.database import Base

# Импортируйте все модели и убедитесь, что они зарегистрированы в Base.metadata
import backend.app.models

# Настройка Alembic
config = context.config

# Получение URL базы данных из наших настроек
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Журнал настройки
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Установить метаданные цели
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Перемещение в автономном режиме"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramestyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Перемещение в режиме онлайн"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()