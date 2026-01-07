# backend/app/schemas/product.py
from pydantic import BaseModel, Field, validator, computed_field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum

class ProductStatus(str, Enum):
    """Перечисление статусов товара"""
    ACTIVE = "active"      
    DRAFT = "draft"          
    OUT_OF_STOCK = "out_of_stock" 
    COMING_SOON = "coming_soon"   
    DISCONTINUED = "discontinued"
    ARCHIVED = "archived"  
    HIDDEN = "hidden"        
    
    @classmethod
    def get_display_name(cls, status: str) -> str:
        """Получить отображаемое название статуса"""
        status_display_map = {
            "active": "В продаже",
            "draft": "Черновик",
            "out_of_stock": "Нет в наличии",
            "coming_soon": "Скоро в продаже",
            "discontinued": "Снят с производства",
            "archived": "Архивирован",
            "hidden": "Скрыт"
        }
        return status_display_map.get(status, status)
    
    @classmethod
    def get_available_statuses(cls) -> Dict[str, str]:
        """Получить все доступные статусы с отображаемыми названиями"""
        return {
            status.value: cls.get_display_name(status.value)
            for status in cls
        }


class ProductImageBase(BaseModel):
    """Базовый класс изображения товара"""
    image_url: str = Field(..., description="URL изображения")
    thumbnail_url: Optional[str] = Field(None, description="URL миниатюры")
    alt_text: Optional[str] = Field(None, max_length=200, description="Альтернативный текст")
    is_primary: bool = Field(False, description="Основное изображение")
    sort_order: int = Field(0, description="Порядок сортировки")


class ProductImageCreate(ProductImageBase):
    """Создание изображения товара"""
    pass


class ProductImageInDB(ProductImageBase):
    """Изображение товара в базе данных"""
    id: int = Field(..., description="ID изображения")
    product_id: int = Field(..., description="ID товара")
    created_at: datetime = Field(..., description="Дата создания")
    
    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    """Базовая информация о товаре"""
    name: str = Field(..., min_length=1, max_length=200, description="Название товара")
    description: Optional[str] = Field(None, description="Описание товара")
    short_description: Optional[str] = Field(None, max_length=500, description="Краткое описание")
    price: float = Field(..., gt=0, description="Цена")
    compare_at_price: Optional[float] = Field(None, gt=0, description="Цена для сравнения")
    cost_price: Optional[float] = Field(None, gt=0, description="Себестоимость")
    sale_price: Optional[float] = Field(None, gt=0, description="Цена со скидкой")
    
    category_id: Optional[int] = Field(None, description="ID категории")
    stock_quantity: int = Field(default=0, ge=0, description="Количество на складе")
    sku: Optional[str] = Field(None, max_length=50, description="SKU код")
    barcode: Optional[str] = Field(None, max_length=100, description="Штрих-код")
    
    # Статусы
    status: Optional[str] = Field("pending", description="Статус товара")
    is_featured: bool = Field(False, description="Рекомендуемый товар")
    is_virtual: bool = Field(False, description="Виртуальный товар")
    requires_shipping: bool = Field(True, description="Требуется доставка")
    
    # Управление запасами
    low_stock_threshold: int = Field(default=5, ge=0, description="Порог низкого запаса")
    manage_stock: bool = Field(True, description="Управлять запасами")
    allow_backorders: bool = Field(False, description="Разрешить предзаказы")
    
    # Физические характеристики
    weight: Optional[float] = Field(None, ge=0, description="Вес")
    weight_unit: str = Field("kg", description="Единица веса")
    length: Optional[float] = Field(None, ge=0, description="Длина")
    width: Optional[float] = Field(None, ge=0, description="Ширина")
    height: Optional[float] = Field(None, ge=0, description="Высота")
    dimensions_unit: str = Field("cm", description="Единица размеров")
    
    # SEO информация
    meta_title: Optional[str] = Field(None, max_length=200, description="Meta заголовок")
    meta_description: Optional[str] = Field(None, description="Meta описание")
    meta_keywords: Optional[str] = Field(None, max_length=500, description="Ключевые слова")
    
    # Теги и атрибуты
    tags: Optional[List[str]] = Field(default_factory=list, description="Список тегов")
    attributes: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Атрибуты товара")
    
    # Дата публикации
    published_at: Optional[datetime] = Field(None, description="Дата публикации")
    
    @validator('price')
    def validate_price(cls, v):
        """Проверка цены"""
        if v <= 0:
            raise ValueError('Цена должна быть больше 0')
        return round(v, 2)
    
    @validator('sku')
    def validate_sku(cls, v):
        """Проверка SKU"""
        if v:
            import re
            if not re.match(r'^[A-Za-z0-9\-_]+$', v):
                raise ValueError('SKU может содержать только буквы, цифры, дефисы и подчеркивания')
        return v


class ProductCreate(ProductBase):
    """Создание товара"""
    # 添加slug字段
    slug: Optional[str] = Field(None, max_length=200, description="URL slug")
    
    @validator('slug')
    def generate_slug(cls, v, values):
        """Генерация slug из названия"""
        if v is None and 'name' in values:
            from slugify import slugify
            return slugify(values['name'])
        return v


class ProductUpdate(BaseModel):
    """Обновление товара"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    compare_at_price: Optional[float] = Field(None, gt=0)
    cost_price: Optional[float] = Field(None, gt=0)
    sale_price: Optional[float] = Field(None, gt=0)
    category_id: Optional[int] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    sku: Optional[str] = Field(None, max_length=50)
    barcode: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = None
    is_featured: Optional[bool] = None
    is_virtual: Optional[bool] = None
    requires_shipping: Optional[bool] = None
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    manage_stock: Optional[bool] = None
    allow_backorders: Optional[bool] = None
    weight: Optional[float] = Field(None, ge=0)
    weight_unit: Optional[str] = None
    length: Optional[float] = Field(None, ge=0)
    width: Optional[float] = Field(None, ge=0)
    height: Optional[float] = Field(None, ge=0)
    dimensions_unit: Optional[str] = None
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = None
    attributes: Optional[Dict[str, Any]] = None
    published_at: Optional[datetime] = None
    slug: Optional[str] = Field(None, max_length=200)


class ProductInDB(ProductBase):
    """Информация о товаре в базе данных"""
    id: int = Field(..., description="ID товара")
    shop_id: int = Field(..., description="ID магазина")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")
    images: List[Any] = Field(default_factory=list, description="Изображения")
    category_name: Optional[str] = Field(None, description="Название категории")
    
    class Config:
        from_attributes = True


class ProductResponse(ProductInDB):
    """Ответ с товаром"""
    
    @computed_field
    @property
    def status_display(self) -> str:
        """Отображаемое название статуса"""
        return ProductStatus.get_display_name(self.status.value)
    
    @computed_field
    @property
    def discount_percentage(self) -> Optional[int]:
        """Процент скидки"""
        if self.original_price and self.original_price > self.price:
            return int(((self.original_price - self.price) / self.original_price) * 100)
        return None
    
    @computed_field
    @property
    def is_discounted(self) -> bool:
        """Есть ли скидка"""
        return self.discount_percentage is not None
    
    @computed_field
    @property
    def is_available(self) -> bool:
        """Доступен ли для покупки"""
        return (
            self.status == ProductStatus.ACTIVE and 
            self.stock_quantity > 0
        )
    
    @computed_field
    @property
    def full_attributes(self) -> Dict[str, Any]:
        """Полные атрибуты товара"""
        attrs = self.attributes.copy()
        
        # Добавляем базовые атрибуты
        attrs.update({
            'weight': self.weight,
            'dimensions': self.dimensions,
            'sku': self.sku
        })
        
        return attrs
    
    class Config:
        from_attributes = True


class ProductList(BaseModel):
    """Ответ со списком товаров"""
    products: List[ProductResponse] = Field(..., description="Список товаров")
    total: int = Field(..., description="Общее количество товаров")
    page: int = Field(..., description="Текущая страница")
    page_size: int = Field(..., description="Размер страницы")
    total_pages: int = Field(..., description="Общее количество страниц")


class ProductSearch(BaseModel):
    """Условия поиска товаров"""
    query: Optional[str] = Field(None, description="Поисковый запрос")
    category_id: Optional[int] = Field(None, description="ID категории")
    min_price: Optional[float] = Field(None, ge=0, description="Минимальная цена")
    max_price: Optional[float] = Field(None, ge=0, description="Максимальная цена")
    status: Optional[str] = Field(None, description="Статус товара")
    is_featured: Optional[bool] = Field(None, description="Рекомендуемый товар")
    tags: Optional[List[str]] = Field(None, description="Теги")
    in_stock: Optional[bool] = Field(None, description="В наличии")
    min_discount: Optional[int] = Field(None, ge=0, le=100, description="Минимальная скидка (%)")
    
    @validator('max_price')
    def validate_max_price(cls, v, values):
        """Проверка максимальной цены"""
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v < values['min_price']:
                raise ValueError('Максимальная цена должна быть больше минимальной')
        return v


class BulkUpdateProduct(BaseModel):
    """Массовое обновление товаров"""
    product_ids: List[int] = Field(..., min_items=1, description="Список ID товаров")
    update_data: ProductUpdate = Field(..., description="Данные для обновления")
    
    @validator('product_ids')
    def validate_product_ids(cls, v):
        """Проверка ID товаров"""
        if len(set(v)) != len(v):
            raise ValueError('ID товаров не должны повторяться')
        return v


class ProductStats(BaseModel):
    """Статистика по товарам"""
    total_products: int = Field(0, description="Общее количество товаров")
    active_products: int = Field(0, description="Активных товаров")
    out_of_stock_products: int = Field(0, description="Товаров нет в наличии")
    discontinued_products: int = Field(0, description="Снято с производства")
    archived_products: int = Field(0, description="Архивированных товаров")
    total_categories: int = Field(0, description="Общее количество категорий")
    average_price: float = Field(0.0, description="Средняя цена")
    total_value: float = Field(0.0, description="Общая стоимость запасов")
    low_stock_products: int = Field(0, description="Товаров с низким запасом")
    new_products_last_30d: int = Field(0, description="Новых товаров за 30 дней")


class ProductImageUpload(BaseModel):
    """Загрузка изображений товара"""
    product_id: int = Field(..., description="ID товара")
    images: List[Dict[str, Any]] = Field(..., min_items=1, description="Список информации об изображениях")
    set_as_primary: Optional[int] = Field(None, ge=0, description="Индекс основного изображения")
    
    @validator('set_as_primary')
    def validate_primary_index(cls, v, values):
        """Проверка индекса основного изображения"""
        if v is not None and 'images' in values:
            if v >= len(values['images']):
                raise ValueError('Индекс основного изображения вне диапазона')
        return v
    
    class Config:
        from_attributes = True


class ProductInventoryUpdate(BaseModel):
    """Обновление запасов товара"""
    quantity_change: int = Field(..., description="Изменение количества")
    operation: str = Field("adjust", description="Тип операции: adjust, increment, decrement")
    reason: Optional[str] = Field(None, max_length=200, description="Причина изменения")
    notes: Optional[str] = Field(None, description="Примечания")
    
    @validator('operation')
    def validate_operation(cls, v):
        """Проверка типа операции"""
        allowed_operations = ["adjust", "increment", "decrement"]
        if v not in allowed_operations:
            raise ValueError(f'Тип операции должен быть одним из: {allowed_operations}')
        return v
    
    @validator('quantity_change')
    def validate_quantity_change(cls, v, values):
        """Проверка изменения количества"""
        if values.get('operation') == 'decrement' and v < 0:
            raise ValueError('Количество для уменьшения не может быть отрицательным')
        return v


class ProductBatchUpdate(BaseModel):
    """Пакетное обновление товаров"""
    product_ids: List[int] = Field(..., min_items=1, max_items=100, description="Список ID товаров")
    update_data: ProductUpdate = Field(..., description="Данные для обновления")
    
    @validator('product_ids')
    def validate_product_ids(cls, v):
        """Проверка ID товаров"""
        if not v:
            raise ValueError('Список ID товаров не может быть пустым')
        if len(v) > 100:
            raise ValueError('Максимальное количество товаров для массового обновления - 100')
        return v


class ProductImportRequest(BaseModel):
    """Запрос на импорт товаров"""
    file_format: Literal["csv", "excel", "json"] = Field("csv", description="Формат файла")
    update_existing: bool = Field(False, description="Обновить существующие товары")
    category_mapping: Optional[Dict[str, int]] = Field(
        None, 
        description="Сопоставление категорий: {название: ID}"
    )
    
    class Config:
        from_attributes = True


class ProductExportRequest(BaseModel):
    """Запрос на экспорт товаров"""
    format: Literal["csv", "excel", "json"] = Field("csv", description="Формат экспорта")
    columns: List[str] = Field(
        default_factory=lambda: [
            "id", "name", "sku", "price", "stock_quantity", 
            "status", "category_id", "created_at"
        ],
        description="Столбцы для экспорта"
    )
    filter: Optional[ProductSearch] = Field(None, description="Фильтры")
    
    @validator('columns')
    def validate_columns(cls, v):
        """Проверка столбцов"""
        allowed_columns = [
            "id", "shop_id", "name", "description", "price", 
            "original_price", "category_id", "stock_quantity", 
            "sku", "status", "is_featured", "is_new", "tags",
            "attributes", "meta_title", "meta_description",
            "created_at", "updated_at", "weight", "dimensions"
        ]
        for col in v:
            if col not in allowed_columns:
                raise ValueError(f'Недопустимый столбец: {col}')
        return v


class ProductStatusUpdate(BaseModel):
    """Обновление статуса товара"""
    status: ProductStatus = Field(..., description="Новый статус")
    reason: Optional[str] = Field(None, max_length=500, description="Причина изменения статуса")
    notes: Optional[str] = Field(None, description="Примечания")


class ProductBulkStatusUpdate(BaseModel):
    """Массовое обновление статуса товаров"""
    product_ids: List[int] = Field(..., min_items=1, description="Список ID товаров")
    status: ProductStatus = Field(..., description="Новый статус")
    reason: Optional[str] = Field(None, max_length=500, description="Причина изменения статуса")


# ИЗМЕНЕНО: Добавлены дополнительные классы для работы с вариантами товаров

class ProductVariantBase(BaseModel):
    """Базовый класс варианта товара"""
    name: str = Field(..., max_length=200, description="Название варианта")
    sku: Optional[str] = Field(None, max_length=50, description="SKU варианта")
    price: float = Field(..., gt=0, description="Цена варианта")
    original_price: Optional[float] = Field(None, gt=0, description="Исходная цена варианта")
    stock_quantity: int = Field(0, ge=0, description="Количество на складе")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Атрибуты варианта")
    weight: Optional[float] = Field(None, ge=0, description="Вес варианта")
    dimensions: Optional[Dict[str, float]] = Field(None, description="Размеры варианта")


class ProductVariantCreate(ProductVariantBase):
    """Создание варианта товара"""
    pass


class ProductVariantUpdate(BaseModel):
    """Обновление варианта товара"""
    name: Optional[str] = Field(None, max_length=200)
    sku: Optional[str] = Field(None, max_length=50)
    price: Optional[float] = Field(None, gt=0)
    original_price: Optional[float] = Field(None, gt=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    attributes: Optional[Dict[str, Any]] = None
    weight: Optional[float] = Field(None, ge=0)
    dimensions: Optional[Dict[str, float]] = None


class ProductVariantResponse(ProductVariantBase):
    """Ответ с вариантом товара"""
    id: int = Field(..., description="ID варианта")
    product_id: int = Field(..., description="ID товара")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")
    
    @computed_field
    @property
    def discount_percentage(self) -> Optional[int]:
        """Процент скидки"""
        if self.original_price and self.original_price > self.price:
            return int(((self.original_price - self.price) / self.original_price) * 100)
        return None
    
    class Config:
        from_attributes = True