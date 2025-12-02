# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.api.v1.endpoints import health, auth, profile, shops  # 新增导入

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="FastAPI Ecommerce Platform - Admin Panel",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["health"])
app.include_router(auth.router, prefix=settings.API_V1_STR + "/auth", tags=["auth"])
app.include_router(profile.router, prefix=settings.API_V1_STR, tags=["profile"])
app.include_router(shops.router, prefix=settings.API_V1_STR, tags=["shops"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Ecommerce Admin API",
        "version": settings.VERSION,
        "docs": "/docs",
        "endpoints": {
            "auth": settings.API_V1_STR + "/auth",
            "profile": settings.API_V1_STR + "/me/profile",
            "shops": settings.API_V1_STR + "/me/shops"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )