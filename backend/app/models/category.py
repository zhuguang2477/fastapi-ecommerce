# backend/app/models/category.py
"""
分类模型
支持多级分类结构
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.database import Base


class Category(Base):
    """Модель категории"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    
    # Информация о категории
    name = Column(String(100), nullable=False, index=True)
    slug = Column(String(100), nullable=False, index=True)  # URL-дружественное имя
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    
    # Иерархическая структура
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    level = Column(Integer, default=0)  # Уровень вложенности, 0 - корневая категория
    path = Column(String(500), nullable=True)  # Путь категории, например "1/2/3"
    
    # Сортировка и отображение
    position = Column(Integer, default=0)  # Позиция сортировки
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)  # Является ли категория избранной
    
    # Метаданные
    meta_title = Column(String(200), nullable=True)
    meta_description = Column(String(500), nullable=True)
    meta_keywords = Column(String(500), nullable=True)
    
    # Статистика
    product_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    shop = relationship("Shop", back_populates="categories")
    parent = relationship("Category", remote_side=[id], backref="children")
    products = relationship("Product", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', shop_id={self.shop_id})>"
    
    @property
    def full_path(self) -> str:
        """Получить полный путь категории"""
        if self.parent and self.parent.path:
            return f"{self.parent.path}/{self.id}"
        return str(self.id)
    
    @property
    def display_name(self) -> str:
        """Получить отображаемое имя (с отступами по уровням)"""
        indent = "  " * self.level
        return f"{indent}{self.name}"
    
    def get_ancestors(self, db_session):
        """Получить всех предков категории"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return list(reversed(ancestors))  # От корня к родителю
    
    def get_descendants(self, db_session):
        """Получить всех потомков категории"""
        from sqlalchemy.orm import Session
        
        def get_children(category_id):
            return db_session.query(Category).filter(
                Category.parent_id == category_id,
                Category.is_active == True
            ).all()
        
        descendants = []
        
        def collect_descendants(category):
            children = get_children(category.id)
            for child in children:
                descendants.append(child)
                collect_descendants(child)
        
        collect_descendants(self)
        return descendants
    
    def to_dict(self, include_relations: bool = False) -> dict:
        """Преобразовать в словарь"""
        result = {
            'id': self.id,
            'shop_id': self.shop_id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'image_url': self.image_url,
            'parent_id': self.parent_id,
            'level': self.level,
            'path': self.path,
            'position': self.position,
            'is_active': self.is_active,
            'is_featured': self.is_featured,
            'product_count': self.product_count,
            'view_count': self.view_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_relations and self.parent:
            result['parent'] = {
                'id': self.parent.id,
                'name': self.parent.name,
                'slug': self.parent.slug
            }
        
        return result


class CategoryStats(Base):
    """Модель статистики категорий (для кэширования статистики)"""
    __tablename__ = "category_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    
    # Статистические поля
    total_products = Column(Integer, default=0)
    active_products = Column(Integer, default=0)
    total_sales = Column(Integer, default=0)
    total_revenue = Column(Integer, default=0)  # Доход (в копейках)
    average_rating = Column(Integer, default=0)  # Средний рейтинг (0-100)
    
    # Временной период
    period_type = Column(String(20), default="all_time")  # daily, weekly, monthly, yearly, all_time
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    
    # Время обновления
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Связи
    category = relationship("Category")
    
    def __repr__(self):
        return f"<CategoryStats(category_id={self.category_id}, total_products={self.total_products})>"