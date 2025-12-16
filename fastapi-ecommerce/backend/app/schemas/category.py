# backend/app/schemas/category.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CategoryBase(BaseModel):
    """Базовая информация о категории"""
    name: str = Field(..., min_length=1, max_length=100, description="Название категории")
    description: Optional[str] = None
    parent_id: Optional[int] = None
    slug: Optional[str] = Field(None, max_length=100, description="URL-дружественное название")

class CategoryCreate(CategoryBase):
    """Создание категории"""
    pass

class CategoryUpdate(BaseModel):
    """Обновление категории"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    slug: Optional[str] = Field(None, max_length=100)

class CategoryInDB(CategoryBase):
    """Информация о категории в базе данных"""
    id: int
    shop_id: int
    created_at: datetime
    updated_at: datetime
    product_count: int = 0  # Количество товаров в данной категории
    subcategories: List['CategoryInDB'] = []  # Подкатегории
    
    class Config:
        from_attributes = True

class CategoryTree(CategoryInDB):
    """Древовидная структура категорий"""
    pass

class CategoryList(BaseModel):
    """Ответ со списком категорий"""
    categories: List[CategoryInDB]
    total: int
    page: int
    page_size: int
    total_pages: int

# Исправление циклических ссылок
CategoryInDB.model_rebuild()