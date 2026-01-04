# backend/app/models/product.py
"""
产品模型
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, Numeric, JSON, Enum as SQLAlchemyEnum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum

from backend.app.database import Base


class ProductStatus(PyEnum):
    """产品状态枚举"""
    IN_STOCK = "в наличии"
    COMING_SOON = "скоро поступит"
    DISCONTINUED = "снят с продажи"
    PENDING = "уточняется"


class Product(Base):
    """Модель товара"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    
    # Основная информация
    name = Column(String(200), nullable=False, index=True)
    slug = Column(String(200), nullable=False, unique=True, index=True)
    sku = Column(String(100), nullable=True, index=True)
    barcode = Column(String(100), nullable=True, index=True) 
    
    # Описательная информация
    short_description = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    
    # Ценовая информация
    price = Column(Numeric(10, 2), nullable=False) 
    sale_price = Column(Numeric(10, 2), nullable=True) 
    cost_price = Column(Numeric(10, 2), nullable=True)
    compare_at_price = Column(Numeric(10, 2), nullable=True)
    
    # Информация о запасах
    stock_quantity = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=5)
    manage_stock = Column(Boolean, default=True) 
    allow_backorders = Column(Boolean, default=False) 
    
    # Статусы
    status = Column(SQLAlchemyEnum(ProductStatus), nullable=True, default=ProductStatus.PENDING)
    is_featured = Column(Boolean, default=False, index=True)
    is_virtual = Column(Boolean, default=False) 
    requires_shipping = Column(Boolean, default=True) 
    
    # Категории и теги
    tags = Column(JSON, nullable=True) 
    attributes = Column(JSON, nullable=True) 
    
    # Вес и размеры (для расчета доставки)
    weight = Column(Numeric(10, 2), nullable=True)
    weight_unit = Column(String(10), default="kg")
    length = Column(Numeric(10, 2), nullable=True)
    width = Column(Numeric(10, 2), nullable=True)
    height = Column(Numeric(10, 2), nullable=True)
    dimensions_unit = Column(String(10), default="cm")
    
    # SEO информация
    meta_title = Column(String(200), nullable=True)
    meta_description = Column(Text, nullable=True)
    meta_keywords = Column(String(500), nullable=True)
    
    # Статистическая информация
    view_count = Column(Integer, default=0)
    order_count = Column(Integer, default=0)
    wishlist_count = Column(Integer, default=0)
    average_rating = Column(Numeric(3, 2), default=0) 
    review_count = Column(Integer, default=0)
    
    # Временная информация
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    shop = relationship("Shop", back_populates="products")
    category = relationship("Category", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")
    basket_items = relationship("BasketItem", back_populates="product", cascade="all, delete-orphan")
    
    # Индексы
    __table_args__ = (
        Index('ix_products_shop_status', 'shop_id', 'status'),
        Index('ix_products_price_range', 'shop_id', 'price', 'sale_price'),
        Index('ix_products_stock_status', 'shop_id', 'stock_quantity', 'status'),
    )

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', shop_id={self.shop_id})>"
    
    @property
    def display_price(self) -> float:
        """Получить отображаемую цену (приоритет у цены со скидкой)"""
        if self.sale_price is not None:
            return float(self.sale_price)
        return float(self.price)
    
    @property
    def is_on_sale(self) -> bool:
        """Действует ли скидка"""
        return self.sale_price is not None and self.sale_price < self.price
    
    @property
    def discount_percentage(self) -> int:
        """Процент скидки"""
        if not self.is_on_sale:
            return 0
        return int((1 - float(self.sale_price) / float(self.price)) * 100)
    
    @property
    def stock_status(self) -> str:
        """Статус запасов"""
        if self.manage_stock:
            if self.stock_quantity <= 0:
                return "out_of_stock"
            elif self.stock_quantity <= self.low_stock_threshold:
                return "low_stock"
            else:
                return "in_stock"
        else:
            return "not_managed"
    
    @property
    def main_image(self) -> str:
        """Получить основное изображение"""
        if self.images:
            # Найти изображение, помеченное как основное
            for image in self.images:
                if image.is_main:
                    return image.url
            # Если нет основного, вернуть первое
            return self.images[0].url
        return None
    
    def to_dict(self, include_relations: bool = False) -> dict:
        """Преобразовать в словарь"""
        result = {
            'id': self.id,
            'shop_id': self.shop_id,
            'category_id': self.category_id,
            'name': self.name,
            'slug': self.slug,
            'sku': self.sku,
            'barcode': self.barcode,
            'short_description': self.short_description,
            'description': self.description,
            'price': float(self.price) if self.price else None,
            'sale_price': float(self.sale_price) if self.sale_price else None,
            'cost_price': float(self.cost_price) if self.cost_price else None,
            'compare_at_price': float(self.compare_at_price) if self.compare_at_price else None,
            'stock_quantity': self.stock_quantity,
            'low_stock_threshold': self.low_stock_threshold,
            'manage_stock': self.manage_stock,
            'allow_backorders': self.allow_backorders,
            'status': self.status.value if self.status else None,
            'is_featured': self.is_featured,
            'is_virtual': self.is_virtual,
            'requires_shipping': self.requires_shipping,
            'tags': self.tags,
            'attributes': self.attributes,
            'weight': float(self.weight) if self.weight else None,
            'weight_unit': self.weight_unit,
            'dimensions': {
                'length': float(self.length) if self.length else None,
                'width': float(self.width) if self.width else None,
                'height': float(self.height) if self.height else None,
                'unit': self.dimensions_unit
            },
            'view_count': self.view_count,
            'order_count': self.order_count,
            'wishlist_count': self.wishlist_count,
            'average_rating': float(self.average_rating) if self.average_rating else 0,
            'review_count': self.review_count,
            'display_price': self.display_price,
            'is_on_sale': self.is_on_sale,
            'discount_percentage': self.discount_percentage,
            'stock_status': self.stock_status,
            'main_image': self.main_image,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_relations:
            if self.category:
                result['category'] = {
                    'id': self.category.id,
                    'name': self.category.name,
                    'slug': self.category.slug
                }
            
            if self.images:
                result['images'] = [
                    {
                        'id': img.id,
                        'url': img.url,
                        'thumbnail_url': img.thumbnail_url,
                        'is_main': img.is_main,
                        'alt_text': img.alt_text,
                        'position': img.position
                    }
                    for img in sorted(self.images, key=lambda x: x.position)
                ]
        
        return result


class ProductImage(Base):
    """Модель изображения товара"""
    __tablename__ = "product_images"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    # Информация об изображении
    url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    alt_text = Column(String(200), nullable=True)
    caption = Column(String(500), nullable=True)
    
    # Настройки отображения
    position = Column(Integer, default=0) 
    is_main = Column(Boolean, default=False) 
    
    # Метаданные
    file_size = Column(Integer, nullable=True) 
    mime_type = Column(String(50), nullable=True)
    dimensions = Column(String(50), nullable=True) 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    product = relationship("Product", back_populates="images")
    
    def __repr__(self):
        return f"<ProductImage(id={self.id}, product_id={self.product_id})>"


class ProductVariant(Base):
    """Модель варианта товара"""
    __tablename__ = "product_variants"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    # Информация о варианте
    name = Column(String(200), nullable=False) 
    sku = Column(String(100), nullable=True, unique=True, index=True)
    
    # Цена и запас (переопределяют значения по умолчанию товара)
    price = Column(Numeric(10, 2), nullable=True) 
    sale_price = Column(Numeric(10, 2), nullable=True)
    stock_quantity = Column(Integer, default=0)
    
    # Комбинация атрибутов
    attributes = Column(JSON, nullable=False) 
    
    # Другие атрибуты
    weight = Column(Numeric(10, 2), nullable=True)
    image_url = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    product = relationship("Product")
    order_items = relationship("OrderItem", back_populates="variant")
    
    def __repr__(self):
        return f"<ProductVariant(id={self.id}, product_id={self.product_id}, name='{self.name}')>"