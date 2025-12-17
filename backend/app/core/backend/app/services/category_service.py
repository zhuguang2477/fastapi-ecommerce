# backend/app/services/category_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import logging

from backend.app.models.category import Category
from backend.app.models.product import Product
from backend.app.schemas.category import CategoryCreate, CategoryUpdate

logger = logging.getLogger(__name__)

class CategoryService:
    """Сервис для работы с категориями"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_category(self, shop_id: int, category_data: CategoryCreate) -> Category:
        """Создание категории"""
        try:
            # Проверка существования родительской категории
            if category_data.parent_id:
                parent_category = self.db.query(Category).filter(
                    Category.id == category_data.parent_id,
                    Category.shop_id == shop_id
                ).first()
                
                if not parent_category:
                    raise ValueError(f"Родительская категория не существует: {category_data.parent_id}")
            
            # Проверка на дублирование названия категории
            existing_category = self.db.query(Category).filter(
                Category.shop_id == shop_id,
                Category.name == category_data.name,
                Category.parent_id == category_data.parent_id
            ).first()
            
            if existing_category:
                raise ValueError(f"Название категории уже существует: {category_data.name}")
            
            # Создание категории
            category = Category(
                shop_id=shop_id,
                **category_data.dict()
            )
            
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)
            
            logger.info(f"Категория успешно создана: {category.name} (ID: {category.id})")
            return category
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при создании категории: {e}")
            raise
    
    def get_category(self, shop_id: int, category_id: int) -> Optional[Category]:
        """Получение одной категории"""
        return self.db.query(Category)\
            .filter(
                Category.id == category_id,
                Category.shop_id == shop_id
            )\
            .first()
    
    def get_categories(
        self,
        shop_id: int,
        skip: int = 0,
        limit: int = 100,
        parent_id: Optional[int] = None,
        include_children: bool = False
    ) -> Tuple[List[Category], int]:
        """Получение списка категорий"""
        query = self.db.query(Category)\
            .filter(Category.shop_id == shop_id)
        
        if parent_id is not None:
            if parent_id == 0:  # Получение корневых категорий
                query = query.filter(Category.parent_id.is_(None))
            else:
                query = query.filter(Category.parent_id == parent_id)
        
        # Получение общего количества
        total = query.count()
        
        # Применение пагинации
        categories = query.order_by(Category.name)\
                         .offset(skip)\
                         .limit(limit)\
                         .all()
        
        # Рекурсивная загрузка дочерних категорий при необходимости
        if include_children and categories:
            for category in categories:
                self._load_children_recursive(category, shop_id)
        
        return categories, total
    
    def get_category_tree(self, shop_id: int) -> List[Category]:
        """Получение полного дерева категорий"""
        # Получение всех корневых категорий
        top_level_categories = self.db.query(Category)\
            .filter(
                Category.shop_id == shop_id,
                Category.parent_id.is_(None)
            )\
            .order_by(Category.name)\
            .all()
        
        # Рекурсивная загрузка дочерних категорий
        for category in top_level_categories:
            self._load_children_recursive(category, shop_id)
        
        return top_level_categories
    
    def _load_children_recursive(self, category: Category, shop_id: int):
        """Рекурсивная загрузка дочерних категорий"""
        children = self.db.query(Category)\
            .filter(
                Category.shop_id == shop_id,
                Category.parent_id == category.id
            )\
            .order_by(Category.name)\
            .all()
        
        category.subcategories = children
        
        # Рекурсивная загрузка дочерних категорий для каждой дочерней
        for child in children:
            self._load_children_recursive(child, shop_id)
        
        # Подсчет количества товаров
        category.product_count = self.db.query(func.count(Product.id))\
            .filter(
                Product.shop_id == shop_id,
                Product.category_id == category.id
            )\
            .scalar() or 0
    
    def update_category(
        self,
        shop_id: int,
        category_id: int,
        update_data: CategoryUpdate
    ) -> Optional[Category]:
        """Обновление категории"""
        category = self.get_category(shop_id, category_id)
        if not category:
            return None
        
        try:
            update_dict = update_data.dict(exclude_unset=True)
            
            # Нельзя сделать категорию родителем самой себя
            if 'parent_id' in update_dict:
                if update_dict['parent_id'] == category_id:
                    raise ValueError("Нельзя сделать категорию родителем самой себя")
                
                # Проверка существования родительской категории
                if update_dict['parent_id']:
                    parent_category = self.db.query(Category).filter(
                        Category.id == update_dict['parent_id'],
                        Category.shop_id == shop_id
                    ).first()
                    
                    if not parent_category:
                        raise ValueError(f"Родительская категория не существует: {update_dict['parent_id']}")
            
            # Проверка на дублирование названия (на одном уровне)
            if 'name' in update_dict:
                existing_category = self.db.query(Category).filter(
                    Category.shop_id == shop_id,
                    Category.name == update_dict['name'],
                    Category.parent_id == (update_dict.get('parent_id') or category.parent_id),
                    Category.id != category_id
                ).first()
                
                if existing_category:
                    raise ValueError(f"Название категории уже существует: {update_dict['name']}")
            
            # Обновление полей категории
            for field, value in update_dict.items():
                setattr(category, field, value)
            
            category.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(category)
            
            logger.info(f"Категория успешно обновлена: {category.name} (ID: {category.id})")
            return category
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при обновлении категории: {e}")
            raise
    
    def delete_category(self, shop_id: int, category_id: int, force: bool = False) -> bool:
        """Удаление категории"""
        category = self.get_category(shop_id, category_id)
        if not category:
            return False
        
        try:
            # Проверка наличия дочерних категорий
            child_count = self.db.query(func.count(Category.id)).filter(
                Category.shop_id == shop_id,
                Category.parent_id == category_id
            ).scalar() or 0
            
            # Проверка наличия товаров в категории
            product_count = self.db.query(func.count(Product.id)).filter(
                Product.shop_id == shop_id,
                Product.category_id == category_id
            ).scalar() or 0
            
            if child_count > 0:
                raise ValueError(f"В этой категории есть {child_count} дочерних категорий. Сначала удалите их.")
            
            if product_count > 0 and not force:
                raise ValueError(f"В этой категории есть {product_count} товаров. Невозможно удалить.")
            
            # Если есть товары и используется принудительное удаление
            if product_count > 0 and force:
                self.db.query(Product)\
                    .filter(
                        Product.shop_id == shop_id,
                        Product.category_id == category_id
                    )\
                    .update({"category_id": None})
            
            # Удаление категории
            self.db.delete(category)
            self.db.commit()
            
            logger.info(f"Категория успешно удалена: {category.name} (ID: {category.id})")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при удалении категории: {e}")
            raise
    
    def move_category(
        self,
        shop_id: int,
        category_id: int,
        new_parent_id: Optional[int]
    ) -> bool:
        """Перемещение категории к новому родителю"""
        category = self.get_category(shop_id, category_id)
        if not category:
            return False
        
        try:
            # Нельзя сделать категорию родителем самой себя
            if new_parent_id == category_id:
                raise ValueError("Нельзя сделать категорию родителем самой себя")
            
            # Проверка существования нового родителя
            if new_parent_id:
                new_parent = self.db.query(Category).filter(
                    Category.id == new_parent_id,
                    Category.shop_id == shop_id
                ).first()
                
                if not new_parent:
                    raise ValueError(f"Родительская категория не существует: {new_parent_id}")
                
                # Проверка на циклические ссылки
                self._check_for_cycles(category, new_parent, shop_id)
            
            # Обновление родительской категории
            category.parent_id = new_parent_id
            category.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Категория успешно перемещена: {category.name} -> ID родителя: {new_parent_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при перемещении категории: {e}")
            raise
    
    def _check_for_cycles(self, category: Category, new_parent: Category, shop_id: int):
        """Проверка на циклические ссылки"""
        current_parent = new_parent
        
        while current_parent:
            if current_parent.id == category.id:
                raise ValueError("Перемещение категории создаст циклическую ссылку")
            
            if not current_parent.parent_id:
                break
                
            current_parent = self.get_category(shop_id, current_parent.parent_id)
    
    def get_category_stats(self, shop_id: int) -> Dict[str, Any]:
        """Получение статистики по категориям"""
        # Общее количество категорий
        total_categories = self.db.query(func.count(Category.id)).filter(
            Category.shop_id == shop_id
        ).scalar() or 0
        
        # Количество корневых категорий
        top_level_categories = self.db.query(func.count(Category.id)).filter(
            Category.shop_id == shop_id,
            Category.parent_id.is_(None)
        ).scalar() or 0
        
        # Максимальная глубина
        # Упрощенная реализация, на практике может потребоваться рекурсивный запрос
        max_depth = 3  # Предполагаем максимальную глубину 3
        
        # Количество категорий с товарами
        categories_with_products = self.db.query(func.count(func.distinct(Product.category_id)))\
            .filter(
                Product.shop_id == shop_id,
                Product.category_id.isnot(None)
            )\
            .scalar() or 0
        
        return {
            "total_categories": total_categories,
            "top_level_categories": top_level_categories,
            "max_depth": max_depth,
            "categories_with_products": categories_with_products,
            "empty_categories": total_categories - categories_with_products
        }