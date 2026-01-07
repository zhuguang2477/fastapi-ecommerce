# backend/app/services/category_service.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, asc, and_, or_
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import logging

from backend.app.models.category import Category
from backend.app.models.product import Product
from backend.app.schemas.category import (
    CategoryCreate, CategoryUpdate, CategoryInDB, 
    CategoryTree, CategoryList, CategoryResponse
)

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
            
            # Проверка на дублирование названия категории на том же уровне
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
    
    def get_category(self, shop_id: int, category_id: int, include_products: bool = False) -> Optional[Category]:
        """Получение одной категории"""
        try:
            query = self.db.query(Category)\
                .filter(
                    Category.id == category_id,
                    Category.shop_id == shop_id
                )
            
            if include_products:
                query = query.options(joinedload(Category.products))
            
            return query.first()
        except Exception as e:
            logger.error(f"Ошибка при получении категории: {e}")
            return None
    
    def get_category_by_slug(self, shop_id: int, slug: str) -> Optional[Category]:
        """Получение категории по slug"""
        try:
            return self.db.query(Category)\
                .filter(
                    Category.shop_id == shop_id,
                    Category.slug == slug
                )\
                .first()
        except Exception as e:
            logger.error(f"Ошибка при получении категории по slug: {e}")
            return None
    
    def get_categories(
        self,
        shop_id: int,
        skip: int = 0,
        limit: int = 100,
        parent_id: Optional[int] = None,
        include_children: bool = False,
        include_products_count: bool = False
    ) -> Tuple[List[Category], int]:
        """Получение списка категорий"""
        try:
            query = self.db.query(Category)\
                .filter(Category.shop_id == shop_id)
            
            if parent_id is not None:
                if parent_id == 0:  # Получение корневых категорий
                    query = query.filter(Category.parent_id.is_(None))
                else:
                    query = query.filter(Category.parent_id == parent_id)
            
            # Получение общего количества
            total = query.count()
            
            # Применение сортировки
            query = query.order_by(Category.sort_order.asc(), Category.name.asc())
            
            # Применение пагинации
            categories = query.offset(skip).limit(limit).all()
            
            # Подсчет количества товаров при необходимости
            if include_products_count and categories:
                for category in categories:
                    category.product_count = self._get_product_count(category.id, shop_id)
            
            # Рекурсивная загрузка дочерних категорий при необходимости
            if include_children and categories:
                for category in categories:
                    self._load_children_recursive(category, shop_id, include_products_count)
            
            return categories, total
            
        except Exception as e:
            logger.error(f"Ошибка при получении списка категорий: {e}")
            raise
    
    def _get_product_count(self, category_id: int, shop_id: int) -> int:
        """Получение количества товаров в категории"""
        return self.db.query(func.count(Product.id))\
            .filter(
                Product.shop_id == shop_id,
                Product.category_id == category_id
            )\
            .scalar() or 0
    
    def get_category_tree(self, shop_id: int, include_products_count: bool = True) -> List[Category]:
        """Получение полного дерева категорий"""
        try:
            # Получение всех категорий магазина
            all_categories = self.db.query(Category)\
                .filter(Category.shop_id == shop_id)\
                .order_by(Category.sort_order.asc(), Category.name.asc())\
                .all()
            
            # Создание словаря для быстрого доступа
            categories_dict = {cat.id: cat for cat in all_categories}
            
            # Инициализация дочерних категорий
            for cat in all_categories:
                cat.subcategories = []
            
            # Построение дерева
            root_categories = []
            for cat in all_categories:
                if cat.parent_id is None:
                    root_categories.append(cat)
                else:
                    parent = categories_dict.get(cat.parent_id)
                    if parent:
                        parent.subcategories.append(cat)
            
            # Подсчет количества товаров
            if include_products_count and all_categories:
                for cat in all_categories:
                    cat.product_count = self._get_product_count(cat.id, shop_id)
            
            return root_categories
            
        except Exception as e:
            logger.error(f"Ошибка при получении дерева категорий: {e}")
            raise
    
    def _load_children_recursive(self, category: Category, shop_id: int, include_products_count: bool = False):
        """Рекурсивная загрузка дочерних категорий"""
        children = self.db.query(Category)\
            .filter(
                Category.shop_id == shop_id,
                Category.parent_id == category.id
            )\
            .order_by(Category.sort_order.asc(), Category.name.asc())\
            .all()
        
        category.subcategories = children
        
        # Подсчет количества товаров
        if include_products_count:
            category.product_count = self._get_product_count(category.id, shop_id)
            for child in children:
                child.product_count = self._get_product_count(child.id, shop_id)
        
        # Рекурсивная загрузка дочерних категорий для каждой дочерней
        for child in children:
            self._load_children_recursive(child, shop_id, include_products_count)
    
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
                if hasattr(category, field):
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
            product_count = self._get_product_count(category_id, shop_id)
            
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
                
                logger.info(f"Удалена привязка {product_count} товаров к категории {category_id}")
            
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
    
    def reorder_categories(self, shop_id: int, category_ids: List[int]) -> bool:
        """Изменение порядка категорий"""
        try:
            # Проверка, что все категории принадлежат магазину
            categories_count = self.db.query(func.count(Category.id))\
                .filter(
                    Category.shop_id == shop_id,
                    Category.id.in_(category_ids)
                )\
                .scalar()
            
            if categories_count != len(category_ids):
                raise ValueError("Некоторые категории не найдены или не принадлежат магазину")
            
            # Обновление порядка
            for index, category_id in enumerate(category_ids, start=1):
                self.db.query(Category)\
                    .filter(
                        Category.id == category_id,
                        Category.shop_id == shop_id
                    )\
                    .update({"sort_order": index})
            
            self.db.commit()
            
            logger.info(f"Порядок категорий успешно изменен: {len(category_ids)} категорий")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при изменении порядка категорий: {e}")
            raise
    
    def get_category_stats(self, shop_id: int) -> Dict[str, Any]:
        """Получение статистики по категориям"""
        try:
            # Общее количество категорий
            total_categories = self.db.query(func.count(Category.id))\
                .filter(Category.shop_id == shop_id)\
                .scalar() or 0
            
            # Количество корневых категорий
            top_level_categories = self.db.query(func.count(Category.id))\
                .filter(
                    Category.shop_id == shop_id,
                    Category.parent_id.is_(None)
                )\
                .scalar() or 0
            
            # Количество категорий с товарами
            categories_with_products = self.db.query(func.count(func.distinct(Product.category_id)))\
                .filter(
                    Product.shop_id == shop_id,
                    Product.category_id.isnot(None)
                )\
                .scalar() or 0
            
            # 创建子查询获取每个类别的商品数量
            product_counts_subquery = self.db.query(
                Product.category_id,
                func.count(Product.id).label('product_count')
            )\
            .filter(
                Product.shop_id == shop_id,
                Product.category_id.isnot(None)
            )\
            .group_by(Product.category_id)\
            .subquery('product_counts')
            
            # 平均数量商品在类别中
            avg_products_per_category = self.db.query(func.avg(product_counts_subquery.c.product_count))\
                .scalar() or 0
            
            # Самая популярная категория (по количеству товаров)
            most_popular_category = self.db.query(
                Category.name,
                func.count(Product.id).label('product_count')
            )\
            .join(Product, Product.category_id == Category.id)\
            .filter(
                Category.shop_id == shop_id,
                Product.shop_id == shop_id
            )\
            .group_by(Category.id, Category.name)\
            .order_by(desc('product_count'))\
            .first()
            
            return {
                "total_categories": total_categories,
                "top_level_categories": top_level_categories,
                "categories_with_products": categories_with_products,
                "empty_categories": total_categories - categories_with_products,
                "avg_products_per_category": float(avg_products_per_category),
                "most_popular_category": {
                    "name": most_popular_category.name if most_popular_category else None,
                    "product_count": most_popular_category.product_count if most_popular_category else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении статистики категорий: {e}")
            raise
    
    def to_response(self, category: Category) -> CategoryResponse:
        """Преобразование категории в схему ответа"""
        if not category:
            return None
        
        return CategoryResponse(
            id=category.id,
            shop_id=category.shop_id,
            name=category.name,
            description=category.description,
            slug=category.slug,
            parent_id=category.parent_id,
            sort_order=category.sort_order,
            is_active=category.is_active,
            meta_title=category.meta_title,
            meta_description=category.meta_description,
            meta_keywords=category.meta_keywords,
            product_count=getattr(category, 'product_count', 0),
            created_at=category.created_at,
            updated_at=category.updated_at
        )
    
    def to_tree_response(self, categories: List[Category]) -> List[CategoryTree]:
        """Преобразование категорий в древовидную структуру"""
        result = []
        
        for category in categories:
            category_tree = CategoryTree(
                **self.to_response(category).dict()
            )
            
            if hasattr(category, 'subcategories') and category.subcategories:
                category_tree.subcategories = self.to_tree_response(category.subcategories)
            
            result.append(category_tree)
        
        return result