#!/usr/bin/env python3
"""
Настроить скрипт проверки
Запуск: python test config.py
"""

import sys
import os

# Добавить корневой каталог проекта в путь Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.app.core.config import settings
    
    print("✅ Настроить успешную загрузку!")
    print(f"📁 Название проекта: {settings.PROJECT_NAME}")
    print(f"🔢 версия: {settings.VERSION}")
    print(f"🐘 Адрес базы данных: {settings.DATABASE_URL}")
    print(f"🔴 Redis URL: {settings.REDIS_URL}")
    print(f"🔑 Ключ JWT: {settings.JWT_SECRET_KEY[:10]}...")
    print(f"🌐 Допустимые источники CORS: {settings.ALLOWED_ORIGINS}")
    print(f"🐛 Режим отладки: {settings.DEBUG}")
    
except Exception as e:
    print(f"❌ Ошибка настройки загрузки: {e}")
    sys.exit(1)