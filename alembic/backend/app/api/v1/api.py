# backend/app/api/v1/api.py
from fastapi import APIRouter
from .endpoints import (
    auth, shops, products, orders, categories,
    customers, basket, shop_settings, design,
    recipients, upload, profile, dashboard, health
)

api_router = APIRouter()

# Обеспечение правильного включения маршрутов
api_router.include_router(auth.router, tags=["Аутентификация"])
api_router.include_router(shops.router, prefix="/shops", tags=["Управление магазинами"])
api_router.include_router(products.router, prefix="", tags=["Управление товарами"])
api_router.include_router(orders.router, prefix="", tags=["Управление заказами"])
api_router.include_router(categories.router, prefix="/categories", tags=["Управление категориями"])
api_router.include_router(customers.router, prefix="/customers", tags=["Управление клиентами"])
api_router.include_router(basket.router, prefix="/baskets", tags=["Управление корзиной"])
api_router.include_router(shop_settings.router, prefix="/shop-settings", tags=["Настройки магазина"])
api_router.include_router(design.router, prefix="/design", tags=["Дизайн магазина"])
api_router.include_router(recipients.router, prefix="/recipients", tags=["Управление получателями"])
api_router.include_router(upload.router, prefix="/upload", tags=["Загрузка файлов"])
api_router.include_router(profile.router, prefix="", tags=["Профиль пользователя"])
api_router.include_router(dashboard.router, prefix="", tags=["Панель управления"])
api_router.include_router(health.router, tags=["Проверка работоспособности"])