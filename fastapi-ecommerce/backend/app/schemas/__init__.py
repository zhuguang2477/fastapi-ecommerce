# backend/app/schemas/__init__.py
from backend.app.schemas.health import HealthCheckResponse, DatabaseHealthResponse, RedisHealthResponse
from backend.app.schemas.user import (
    UserBase,
    UserCreate,
    UserResponse,
    UserUpdate,
    Token,
    TokenData
)
from backend.app.schemas.otp import OTPRequest, OTPVerify, TokenResponse
from backend.app.schemas.auth import SendOTPRequest, ConfirmOTPRequest
from backend.app.schemas.profile import ProfileUpdate, ProfileResponse
from backend.app.schemas.shop import ShopCreate, ShopJoinRequest, ShopResponse, ShopMemberResponse
from backend.app.schemas.dashboard import DashboardStats, CategoryStat, MonthlyRevenue, UserActivity
from backend.app.schemas.order import (
    OrderCreate, OrderInDB, OrderUpdate, OrderList, 
    OrderStats, DailyOrderStats, OrderStatus, 
    PaymentStatus, PaymentMethod, Address, 
    OrderItemCreate, OrderItemInDB,
    OrderFilter, OrderSearch, OrderBulkUpdate,
    OrderStatusUpdate, OrderExportRequest  # Новый
)
from backend.app.schemas.product import (
    ProductBase, ProductCreate, ProductUpdate, ProductInDB,
    ProductResponse, ProductList, ProductSearch, BulkUpdateProduct,
    ProductStats, ProductStatus, ProductImageCreate, ProductImageInDB
)
from backend.app.schemas.category import (
    CategoryBase, CategoryCreate, CategoryUpdate, CategoryInDB,
    CategoryTree, CategoryList
)
from backend.app.schemas.upload import (
    UploadResponse, MultipleUploadResponse, 
    ImageUploadRequest, FileUploadConfig
)
from backend.app.schemas.dashboard import (
    DashboardStats, CategoryStat, MonthlyRevenue, 
    UserActivity, QuickStats, WeeklyActivity
)
# Добавить импорт
from backend.app.schemas.customer import (
    CustomerResponse, CustomerDetail, CustomerList,
    CustomerStats, CustomerFilter, CustomerSearch,
    CustomerStatus, CustomerType
)

from backend.app.schemas.settings import (
    ShopSettingsBase, ShopSettingsCreate, ShopSettingsUpdate, ShopSettingsResponse,
    SocialLinks
)
from backend.app.schemas.design import (
    ShopDesignBase, ShopDesignCreate, ShopDesignUpdate, ShopDesignResponse,
    HeroBanner, UploadLogoRequest
)

__all__ = [
    # Существующие схемы
    "HealthCheckResponse",
    "DatabaseHealthResponse", 
    "RedisHealthResponse",
    "UserBase",
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    "Token",
    "TokenData",
    "OTPRequest",
    "OTPVerify",
    "TokenResponse",
    "SendOTPRequest",
    "ConfirmOTPRequest",
    "ProfileUpdate",
    "ProfileResponse",
    "ShopCreate",
    "ShopJoinRequest",
    "ShopResponse",
    "ShopMemberResponse",
    
    # Новые схемы
    "DashboardStats",
    "CategoryStat",
    "MonthlyRevenue",
    "UserActivity",
    
    # Связанные с заказами
    "OrderCreate",
    "OrderInDB",
    "OrderUpdate",
    "OrderList",
    "OrderStats",
    "DailyOrderStats",
    "OrderStatus",
    "PaymentStatus",
    "PaymentMethod",
    "Address",
    "OrderItemCreate",
    "OrderItemInDB",
    
    # Связанные с товарами
    "ProductBase",
    "ProductCreate",
    "ProductUpdate",
    "ProductInDB",
    "ProductResponse",
    "ProductList",
    "ProductSearch",
    "BulkUpdateProduct",
    "ProductStats",
    "ProductStatus",
    "ProductImageCreate",
    "ProductImageInDB",
    
    # Связанные с категориями
    "CategoryBase",
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryInDB",
    "CategoryTree",
    "CategoryList",
    
    # Связанные с загрузкой
    "UploadResponse",
    "MultipleUploadResponse",
    "ImageUploadRequest",
    "FileUploadConfig",

    "DashboardStats", "CategoryStat", "MonthlyRevenue",
    "UserActivity", "QuickStats", "WeeklyActivity",

    "OrderFilter", "OrderSearch", "OrderBulkUpdate",
    "OrderStatusUpdate", "OrderExportRequest",

    "CustomerResponse", "CustomerDetail", "CustomerList",
    "CustomerStats", "CustomerFilter", "CustomerSearch",
    "CustomerStatus", "CustomerType",

    "ShopSettingsBase", "ShopSettingsCreate", "ShopSettingsUpdate", "ShopSettingsResponse",
    "SocialLinks",
    "ShopDesignBase", "ShopDesignCreate", "ShopDesignUpdate", "ShopDesignResponse",
    "HeroBanner", "UploadLogoRequest",
]