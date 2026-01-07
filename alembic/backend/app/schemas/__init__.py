# backend/app/schemas/__init__.py
from backend.app.schemas.health import HealthCheckResponse, DatabaseHealthResponse, RedisHealthResponse
from backend.app.schemas.user import (
    UserBase,
    UserCreate,
    UserResponse,
    UserUpdate,
    Token,
    TokenData,
    UserProfile,
    OTPVerificationStatus,
    UserWithOTPStatus
)
from backend.app.schemas.otp import OTPRequest, OTPVerify, TokenResponse, OTPStatusResponse
from backend.app.schemas.auth import SendOTPRequest, ConfirmOTPRequest, CompleteProfileRequest, RegisterRequest
from backend.app.schemas.profile import ProfileUpdate, ProfileResponse
from backend.app.schemas.shop import ShopCreate, ShopJoinRequest, ShopResponse, ShopMemberResponse
from backend.app.schemas.dashboard import DashboardStats, CategoryStat, MonthlyRevenue, UserActivity
from backend.app.schemas.order import (
    OrderCreate, OrderInDB, OrderUpdate, OrderList, 
    OrderStats, DailyOrderStats, OrderStatus, 
    PaymentStatus, PaymentMethod, Address, 
    OrderItemCreate, OrderItemInDB,
    OrderFilter, OrderSearch, OrderBulkUpdate,
    OrderStatusUpdate, OrderExportRequest
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
# 客户模式
from backend.app.schemas.customer import (
    CustomerResponse, CustomerDetail, CustomerList,
    CustomerStats, CustomerFilter, CustomerSearch,
    CustomerStatus, CustomerType, CustomerBase
)
# 店铺设置模式
from backend.app.schemas.shop_settings import (
    ShopSettingsBase, ShopSettingsCreate, ShopSettingsUpdate, ShopSettingsResponse
)
# 店铺设计模式
from backend.app.schemas.shop_design import (
    ShopDesignBase, ShopDesignCreate, ShopDesignUpdate, ShopDesignResponse,
    HeroBanner, UploadLogoRequest, ThemeColor, FontFamily, LayoutStyle
)
# 收货人模式
from backend.app.schemas.recipient import (
    RecipientBase, RecipientCreate, RecipientUpdate, RecipientInDB, 
    RecipientResponse, RecipientList
)
# 购物车模式
from backend.app.schemas.basket import (
    BasketStatus, BasketBase, BasketCreate, BasketUpdate, 
    BasketItemBase, BasketItemCreate, BasketItemUpdate, 
    BasketItemResponse, BasketResponse, BasketList
)

__all__ = [
    # 健康检查
    "HealthCheckResponse",
    "DatabaseHealthResponse", 
    "RedisHealthResponse",
    
    # 用户
    "UserBase",
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    "Token",
    "TokenData",
    "UserProfile",
    "OTPVerificationStatus",
    "UserWithOTPStatus",
    
    # OTP
    "OTPRequest",
    "OTPVerify",
    "TokenResponse",
    "OTPStatusResponse",
    
    # 认证
    "SendOTPRequest",
    "ConfirmOTPRequest",
    "CompleteProfileRequest",
    "RegisterRequest",
    
    # 个人资料
    "ProfileUpdate",
    "ProfileResponse",
    
    # 店铺
    "ShopCreate",
    "ShopJoinRequest",
    "ShopResponse",
    "ShopMemberResponse",
    
    # 仪表板
    "DashboardStats",
    "CategoryStat",
    "MonthlyRevenue",
    "UserActivity",
    "QuickStats",
    "WeeklyActivity",
    
    # 订单
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
    "OrderFilter",
    "OrderSearch",
    "OrderBulkUpdate",
    "OrderStatusUpdate",
    "OrderExportRequest",
    
    # 产品
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
    
    # 分类
    "CategoryBase",
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryInDB",
    "CategoryTree",
    "CategoryList",
    
    # 上传
    "UploadResponse",
    "MultipleUploadResponse",
    "ImageUploadRequest",
    "FileUploadConfig",
    
    # 客户
    "CustomerBase",
    "CustomerResponse",
    "CustomerDetail",
    "CustomerList",
    "CustomerStats",
    "CustomerFilter",
    "CustomerSearch",
    "CustomerStatus",
    "CustomerType",
    
    # 店铺设置
    "ShopSettingsBase",
    "ShopSettingsCreate",
    "ShopSettingsUpdate",
    "ShopSettingsResponse",
    "SocialLinks",
    
    # 店铺设计
    "ShopDesignBase",
    "ShopDesignCreate",
    "ShopDesignUpdate",
    "ShopDesignResponse",
    "HeroBanner",
    "UploadLogoRequest",
    "ThemeColor",
    "FontFamily",
    "LayoutStyle",
    
    # 收货人
    "RecipientBase",
    "RecipientCreate",
    "RecipientUpdate",
    "RecipientInDB",
    "RecipientResponse",
    "RecipientList",
    
    # 购物车
    "BasketStatus",
    "BasketBase",
    "BasketCreate",
    "BasketUpdate",
    "BasketItemBase",
    "BasketItemCreate",
    "BasketItemUpdate",
    "BasketItemResponse",
    "BasketResponse",
    "BasketList"
]