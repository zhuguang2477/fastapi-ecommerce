# backend/app/api/v1/api.py
from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    auth, upload, shops, health, customers,
    categories, profile, products, orders, dashboard, settings, design
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Аутентификация"])
api_router.include_router(profile.router, prefix="/profile", tags=["Профиль"])
api_router.include_router(shops.router, prefix="/shops", tags=["Магазины"])
api_router.include_router(products.router, prefix="/products", tags=["Товары"])
api_router.include_router(categories.router, prefix="/categories", tags=["Категории"])
api_router.include_router(orders.router, prefix="/orders", tags=["Заказы"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Панель управления"])
api_router.include_router(upload.router, prefix="/upload", tags=["Загрузка"])
api_router.include_router(health.router, prefix="/health", tags=["Проверка состояния"])
api_router.include_router(customers.router, prefix="/customers", tags=["Клиенты"]) 
api_router.include_router(settings.router, prefix="/settings", tags=["Настройки магазина"]) 
api_router.include_router(design.router, prefix="/design", tags=["Дизайн магазина"])