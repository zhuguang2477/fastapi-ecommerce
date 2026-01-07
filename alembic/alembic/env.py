# alembic/env.py
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 加载 .env 文件
from dotenv import load_dotenv

from backend.app.models import Base

# 加载环境变量
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# 动态导入 settings 以获取数据库配置
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from backend.app.core.config import settings
    DATABASE_URL = settings.DATABASE_URL
except ImportError as e:
    print(f"警告：无法导入 settings: {e}")
    # 回退到环境变量
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        # 使用默认值
        DATABASE_URL = "postgresql://postgres@localhost:5432/ecommerce_db"
        print(f"警告：使用默认数据库 URL: {DATABASE_URL}")

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# 设置数据库 URL
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 重要：导入你的 Base 和所有模型
# 确保所有模型都被导入，以便 Alembic 能检测到它们

# 导入你的 Base 和所有模型
from backend.app.database import Base
from backend.app.models import base, user, otp, order, product, customer, category, shop, analytics, shop_settings

# 设置 target_metadata
target_metadata = Base.metadata

# 其他配置
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            compare_type=True,  # 检测类型变化
            compare_server_default=True,  # 检测默认值变化
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()