# backend/app/api/v1/api.py
from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    auth, upload, shops, health, customers,
    categories, profile, products, orders, dashboard, settings, design
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(shops.router, prefix="/shops", tags=["shops"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(orders.router, prefix="/orders", tags=["rders"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"]) 
api_router.include_router(settings.router, prefix="/settings", tags=["settings"]) 
api_router.include_router(design.router, prefix="/design", tags=["design"])