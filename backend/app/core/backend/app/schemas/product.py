# backend/app/schemas/product.py
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum

class ProductStatus(str, Enum):
    """Перечисление статусов товара"""
    ACTIVE = "active"           # В продаже
    OUT_OF_STOCK = "out_of_stock"  # Нет в наличии
    COMING_SOON = "coming_soon"    # Скоро в продаже
    DISCONTINUED = "discontinued"  # Снят с производства
    PENDING = "pending"        # На рассмотрении

class ProductImageBase(BaseModel):
    """Базовый класс изображения товара"""
    image_url: str
    thumbnail_url: Optional[str] = None
    alt_text: Optional[str] = None
    is_primary: bool = False

class ProductImageCreate(ProductImageBase):
    pass

class ProductImageInDB(ProductImageBase):
    id: int
    product_id: int
    sort_order: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    """Базовая информация о товаре"""
    name: str = Field(..., min_length=1, max_length=200, description="Название товара")
    description: Optional[str] = None
    price: float = Field(..., gt=0, description="Цена")
    original_price: Optional[float] = Field(None, gt=0, description="Исходная цена")
    category_id: Optional[int] = None
    stock_quantity: int = Field(default=0, ge=0, description="Количество на складе")
    sku: Optional[str] = Field(None, max_length=50, description="SKU код")
    
    # Теги и атрибуты
    tags: List[str] = Field(default_factory=list, description="Список тегов")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Атрибуты товара")
    
    # SEO информация
    meta_title: Optional[str] = Field(None, max_length=200, description="Meta заголовок")
    meta_description: Optional[str] = Field(None, description="Meta описание")

class ProductCreate(ProductBase):
    """Создание товара"""
    status: ProductStatus = ProductStatus.ACTIVE
    is_featured: bool = False
    is_new: bool = True

class ProductUpdate(BaseModel):
    """Обновление товара"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    original_price: Optional[float] = Field(None, gt=0)
    category_id: Optional[int] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    sku: Optional[str] = Field(None, max_length=50)
    status: Optional[ProductStatus] = None
    is_featured: Optional[bool] = None
    is_new: Optional[bool] = None
    tags: Optional[List[str]] = None
    attributes: Optional[Dict[str, Any]] = None
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = None

class ProductInDB(ProductBase):
    """Информация о товаре в базе данных"""
    id: int
    shop_id: int
    status: ProductStatus
    is_featured: bool
    is_new: bool
    created_at: datetime
    updated_at: datetime
    images: List[ProductImageInDB] = []
    category_name: Optional[str] = None  # Название категории
    
    class Config:
        from_attributes = True

class ProductResponse(ProductInDB):
    """Ответ с товаром"""
    pass

class ProductList(BaseModel):
    """Ответ со списком товаров"""
    products: List[ProductInDB]
    total: int
    page: int
    page_size: int
    total_pages: int

class ProductSearch(BaseModel):
    """Условия поиска товаров"""
    query: Optional[str] = None
    category_id: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    status: Optional[ProductStatus] = None
    is_featured: Optional[bool] = None
    is_new: Optional[bool] = None
    tags: Optional[List[str]] = None
    in_stock: Optional[bool] = None

class BulkUpdateProduct(BaseModel):
    """Массовое обновление товаров"""
    product_ids: List[int]
    update_data: ProductUpdate

class ProductStats(BaseModel):
    """Статистика по товарам"""
    total_products: int
    active_products: int
    out_of_stock_products: int
    discontinued_products: int
    total_categories: int
    average_price: float
    total_value: float  # Общая стоимость запасов

    # Добавьте следующее содержимое в backend/app/schemas/product.py

class ProductImageUpload(BaseModel):
    """Загрузка изображений товара"""
    product_id: int
    images: List[Dict[str, Any]]  # Список информации об изображениях
    set_as_primary: Optional[int] = None  # Индекс изображения, устанавливаемого как основное
    
    class Config:
        from_attributes = True


class ProductInventoryUpdate(BaseModel):
    """Обновление запасов товара"""
    quantity_change: int
    operation: str = "adjust"  # adjust, increment, decrement
    reason: Optional[str] = None
    notes: Optional[str] = None
    
    @validator('operation')
    def validate_operation(cls, v):
        allowed_operations = ["adjust", "increment", "decrement"]
        if v not in allowed_operations:
            raise ValueError(f'Тип операции должен быть одним из: {allowed_operations}')
        return v
    
    @validator('quantity_change')
    def validate_quantity_change(cls, v, values):
        if values.get('operation') == 'decrement' and v < 0:
            raise ValueError('Количество для уменьшения не может быть отрицательным')
        return v


class ProductBatchUpdate(BaseModel):
    """Пакетное обновление товаров"""
    product_ids: List[int]
    update_data: ProductUpdate
    
    @validator('product_ids')
    def validate_product_ids(cls, v):
        if not v:
            raise ValueError('Список ID товаров не может быть пустым')
        if len(v) > 100:
            raise ValueError('Максимальное количество товаров для массового обновления - 100')
        return v


class ProductImportRequest(BaseModel):
    """Запрос на импорт товаров"""
    file_format: Literal["csv", "excel", "json"] = "csv"
    update_existing: bool = False
    category_mapping: Optional[Dict[str, int]] = None
    
    class Config:
        from_attributes = True


class ProductExportRequest(BaseModel):
    """Запрос на экспорт товаров"""
    format: Literal["csv", "excel", "json"] = "csv"
    columns: List[str] = Field(default_factory=lambda: [
        "id", "name", "sku", "price", "stock_quantity", 
        "status", "category_id", "created_at"
    ])
    filter: Optional[ProductSearch] = None
    
    @validator('columns')
    def validate_columns(cls, v):
        allowed_columns = [
            "id", "shop_id", "name", "description", "price", 
            "original_price", "category_id", "stock_quantity", 
            "sku", "status", "is_featured", "is_new", "tags",
            "attributes", "meta_title", "meta_description",
            "created_at", "updated_at"
        ]
        for col in v:
            if col not in allowed_columns:
                raise ValueError(f'Недопустимый столбец: {col}')
        return v