# backend/app/services/product_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_, update, select
from sqlalchemy.orm import joinedload
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import logging

from backend.app.models.product import Product, ProductImage
from backend.app.models.category import Category
from backend.app.schemas.product import ProductCreate, ProductUpdate, ProductSearch, ProductStatus

logger = logging.getLogger(__name__)

class ProductService:
    """Сервисный класс для работы с товарами"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_product(self, shop_id: int, product_data: ProductCreate) -> Product:
        """Создание товара"""
        try:
            # Проверка существования категории (если предоставлен category_id)
            if product_data.category_id:
                category = self.db.query(Category).filter(
                    Category.id == product_data.category_id,
                    Category.shop_id == shop_id
                ).first()
                
                if not category:
                    raise ValueError(f"Категория не найдена: {product_data.category_id}")
            
            # Создание товара
            product = Product(
                shop_id=shop_id,
                **product_data.dict(exclude={'images'})
            )
            
            self.db.add(product)
            self.db.flush()  # Получение product.id
            
            # Если есть данные изображений, их можно добавить здесь
            # Изображения обычно загружаются через отдельный API
            
            self.db.commit()
            self.db.refresh(product)
            
            logger.info(f"Товар успешно создан: {product.name} (ID: {product.id})")
            return product
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при создании товара: {e}")
            raise
    
    def get_product(self, shop_id: int, product_id: int) -> Optional[Product]:
        """Получение одного товара (включая изображения и информацию о категории)"""
        return self.db.query(Product)\
            .options(
                joinedload(Product.images),
                joinedload(Product.category)
            )\
            .filter(
                Product.id == product_id,
                Product.shop_id == shop_id
            )\
            .first()
    
    def get_products(
        self,
        shop_id: int,
        skip: int = 0,
        limit: int = 100,
        search_params: Optional[ProductSearch] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Product], int]:
        """Получение списка товаров"""
        query = self.db.query(Product)\
            .options(joinedload(Product.images))\
            .filter(Product.shop_id == shop_id)
        
        # Применение условий поиска
        if search_params:
            if search_params.query:
                search_term = f"%{search_params.query}%"
                query = query.filter(
                    or_(
                        Product.name.ilike(search_term),
                        Product.description.ilike(search_term),
                        Product.sku.ilike(search_term)
                    )
                )
            
            if search_params.category_id:
                query = query.filter(Product.category_id == search_params.category_id)
            
            if search_params.min_price:
                query = query.filter(Product.price >= search_params.min_price)
            
            if search_params.max_price:
                query = query.filter(Product.price <= search_params.max_price)
            
            if search_params.status:
                query = query.filter(Product.status == search_params.status)
            
            if search_params.is_featured is not None:
                query = query.filter(Product.is_featured == search_params.is_featured)
            
            if search_params.is_new is not None:
                query = query.filter(Product.is_new == search_params.is_new)
            
            if search_params.in_stock is not None:
                if search_params.in_stock:
                    query = query.filter(Product.stock_quantity > 0)
                else:
                    query = query.filter(Product.stock_quantity == 0)
            
            if search_params.tags:
                # Простая фильтрация по тегам (предполагается, что tags - JSON-массив)
                for tag in search_params.tags:
                    query = query.filter(Product.tags.contains([tag]))
        
        # Получение общего количества
        total = query.count()
        
        # Применение сортировки
        if sort_by == "name":
            order_by = Product.name
        elif sort_by == "price":
            order_by = Product.price
        elif sort_by == "created_at":
            order_by = Product.created_at
        elif sort_by == "updated_at":
            order_by = Product.updated_at
        else:
            order_by = Product.created_at
        
        if sort_order == "desc":
            order_by = desc(order_by)
        
        # Применение пагинации
        products = query.order_by(order_by)\
                       .offset(skip)\
                       .limit(limit)\
                       .all()
        
        return products, total
    
    def update_product(
        self,
        shop_id: int,
        product_id: int,
        update_data: ProductUpdate
    ) -> Optional[Product]:
        """Обновление товара"""
        product = self.get_product(shop_id, product_id)
        if not product:
            return None
        
        try:
            update_dict = update_data.dict(exclude_unset=True)
            
            # Если обновлен category_id, проверка существования категории
            if 'category_id' in update_dict and update_dict['category_id']:
                category = self.db.query(Category).filter(
                    Category.id == update_dict['category_id'],
                    Category.shop_id == shop_id
                ).first()
                
                if not category:
                    raise ValueError(f"Категория не найдена: {update_dict['category_id']}")
            
            # Обновление полей товара
            for field, value in update_dict.items():
                setattr(product, field, value)
            
            product.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(product)
            
            logger.info(f"Товар успешно обновлен: {product.name} (ID: {product.id})")
            return product
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при обновлении товара: {e}")
            raise
    
    def delete_product(self, shop_id: int, product_id: int) -> bool:
        """Удаление товара (мягкое удаление)"""
        product = self.get_product(shop_id, product_id)
        if not product:
            return False
        
        try:
            # Мягкое удаление: изменение статуса на "снят с производства"
            product.status = ProductStatus.DISCONTINUED
            product.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"Товар снят с продажи: {product.name} (ID: {product.id})")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при удалении товара: {e}")
            return False
    
    def bulk_update_products(
        self,
        shop_id: int,
        product_ids: List[int],
        update_data: ProductUpdate
    ) -> int:
        """Массовое обновление товаров"""
        try:
            # Проверка, что все товары принадлежат данному магазину
            valid_products = self.db.query(Product).filter(
                Product.id.in_(product_ids),
                Product.shop_id == shop_id
            ).count()
            
            if valid_products != len(product_ids):
                raise ValueError("Некоторые товары не существуют или не принадлежат данному магазину")
            
            # Формирование данных для обновления
            update_dict = update_data.dict(exclude_unset=True)
            update_dict['updated_at'] = datetime.utcnow()
            
            # Выполнение массового обновления
            result = self.db.query(Product).filter(
                Product.id.in_(product_ids),
                Product.shop_id == shop_id
            ).update(update_dict, synchronize_session=False)
            
            self.db.commit()
            logger.info(f"Массово обновлено {result} товаров")
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при массовом обновлении товаров: {e}")
            raise
    
    def get_product_stats(self, shop_id: int) -> Dict[str, Any]:
        """Получение статистики по товарам"""
        # Общее количество товаров
        total_products = self.db.query(func.count(Product.id)).filter(
            Product.shop_id == shop_id
        ).scalar() or 0
        
        # Количество товаров по статусам
        status_stats = {}
        for status in ProductStatus:
            count = self.db.query(func.count(Product.id)).filter(
                Product.shop_id == shop_id,
                Product.status == status
            ).scalar() or 0
            status_stats[status] = count
        
        # Средняя цена
        avg_price = self.db.query(func.avg(Product.price)).filter(
            Product.shop_id == shop_id,
            Product.status == ProductStatus.ACTIVE
        ).scalar() or 0
        
        # Общая стоимость запасов
        total_value_result = self.db.query(
            func.sum(Product.price * Product.stock_quantity)
        ).filter(
            Product.shop_id == shop_id,
            Product.status == ProductStatus.ACTIVE
        ).scalar() or 0
        
        # Общее количество категорий
        total_categories = self.db.query(func.count(Category.id)).filter(
            Category.shop_id == shop_id
        ).scalar() or 0
        
        return {
            "total_products": total_products,
            "status_stats": status_stats,
            "average_price": float(avg_price),
            "total_value": float(total_value_result),
            "total_categories": total_categories
        }
    
    def update_product_images(
        self,
        shop_id: int,
        product_id: int,
        images_data: List[Dict[str, Any]]
    ) -> bool:
        """Обновление изображений товара"""
        product = self.get_product(shop_id, product_id)
        if not product:
            return False
        
        try:
            # Удаление существующих изображений
            self.db.query(ProductImage).filter(
                ProductImage.product_id == product_id
            ).delete()
            
            # Добавление новых изображений
            for idx, image_data in enumerate(images_data):
                product_image = ProductImage(
                    product_id=product_id,
                    image_url=image_data['url'],
                    thumbnail_url=image_data.get('thumbnail_url'),
                    alt_text=image_data.get('alt_text', product.name),
                    is_primary=image_data.get('is_primary', idx == 0),
                    sort_order=idx
                )
                self.db.add(product_image)
            
            self.db.commit()
            logger.info(f"Обновлены изображения товара {product_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при обновлении изображений товара: {e}")
            return False
    
    def adjust_stock(
        self,
        shop_id: int,
        product_id: int,
        quantity_change: int,
        operation: str = "adjust"  # adjust, increment, decrement
    ) -> bool:
        """Корректировка запасов"""
        product = self.get_product(shop_id, product_id)
        if not product:
            return False
        
        try:
            if operation == "adjust":
                new_quantity = quantity_change
            elif operation == "increment":
                new_quantity = product.stock_quantity + quantity_change
            elif operation == "decrement":
                new_quantity = product.stock_quantity - quantity_change
            else:
                raise ValueError(f"Неподдерживаемая операция: {operation}")
            
            if new_quantity < 0:
                raise ValueError("Количество запасов не может быть отрицательным")
            
            product.stock_quantity = new_quantity
            
            # Автоматическое обновление статуса на основе количества запасов
            if new_quantity == 0:
                product.status = ProductStatus.OUT_OF_STOCK
            elif product.status == ProductStatus.OUT_OF_STOCK and new_quantity > 0:
                product.status = ProductStatus.ACTIVE
            
            product.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Скорректированы запасы товара {product_id}: {product.stock_quantity}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при корректировке запасов: {e}")
            return False
        
        # Добавление следующих методов в backend/app/services/product_service.py

def get_products_by_ids(self, shop_id: int, product_ids: List[int]) -> List[Product]:
    """Получение товаров по списку ID"""
    try:
        products = self.db.query(Product)\
            .options(joinedload(Product.images))\
            .filter(
                Product.shop_id == shop_id,
                Product.id.in_(product_ids)
            ).all()
        return products
    except Exception as e:
        logger.error(f"Ошибка при получении товаров по списку ID: {e}")
        return []


def update_product_status(
    self,
    shop_id: int,
    product_id: int,
    status: ProductStatus,
    reason: Optional[str] = None
) -> bool:
    """Обновление статуса товара"""
    try:
        product = self.get_product(shop_id, product_id)
        if not product:
            return False
        
        old_status = product.status
        product.status = status
        
        # Запись изменения статуса
        if hasattr(product, 'status_history'):
            history_entry = {
                'old_status': old_status,
                'new_status': status,
                'changed_at': datetime.utcnow(),
                'reason': reason
            }
            
            if not product.status_history:
                product.status_history = [history_entry]
            else:
                product.status_history.append(history_entry)
        
        product.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Статус товара {product_id} изменен с {old_status} на {status}")
        return True
        
    except Exception as e:
        self.db.rollback()
        logger.error(f"Ошибка при обновлении статуса товара: {e}")
        return False


def get_low_stock_products(
    self,
    shop_id: int,
    threshold: int = 10
) -> List[Product]:
    """Получение товаров с низким запасом"""
    try:
        products = self.db.query(Product)\
            .options(joinedload(Product.images))\
            .filter(
                Product.shop_id == shop_id,
                Product.stock_quantity <= threshold,
                Product.stock_quantity > 0,
                Product.status == ProductStatus.ACTIVE
            ).all()
        return products
    except Exception as e:
        logger.error(f"Ошибка при получении товаров с низким запасом: {e}")
        return []


def get_out_of_stock_products(self, shop_id: int) -> List[Product]:
    """Получение отсутствующих товаров"""
    try:
        products = self.db.query(Product)\
            .options(joinedload(Product.images))\
            .filter(
                Product.shop_id == shop_id,
                Product.stock_quantity <= 0,
                Product.status == ProductStatus.ACTIVE
            ).all()
        return products
    except Exception as e:
        logger.error(f"Ошибка при получении отсутствующих товаров: {e}")
        return []


def update_product_attributes(
    self,
    shop_id: int,
    product_id: int,
    attributes: Dict[str, Any]
) -> bool:
    """Обновление атрибутов товара"""
    try:
        product = self.get_product(shop_id, product_id)
        if not product:
            return False
        
        # Объединение с существующими атрибутами
        existing_attributes = product.attributes or {}
        existing_attributes.update(attributes)
        product.attributes = existing_attributes
        
        product.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Обновлены атрибуты товара {product_id}")
        return True
        
    except Exception as e:
        self.db.rollback()
        logger.error(f"Ошибка при обновлении атрибутов товара: {e}")
        return False


def update_product_tags(
    self,
    shop_id: int,
    product_id: int,
    tags: List[str],
    operation: str = "replace"  # replace, add, remove
) -> bool:
    """Обновление тегов товара"""
    try:
        product = self.get_product(shop_id, product_id)
        if not product:
            return False
        
        existing_tags = product.tags or []
        
        if operation == "replace":
            new_tags = tags
        elif operation == "add":
            new_tags = list(set(existing_tags + tags))
        elif operation == "remove":
            new_tags = [tag for tag in existing_tags if tag not in tags]
        else:
            raise ValueError(f"Неподдерживаемая операция: {operation}")
        
        product.tags = new_tags
        product.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Обновлены теги товара {product_id}: {operation}")
        return True
        
    except Exception as e:
        self.db.rollback()
        logger.error(f"Ошибка при обновлении тегов товара: {e}")
        return False


def duplicate_product(
    self,
    shop_id: int,
    product_id: int,
    new_name: Optional[str] = None
) -> Optional[Product]:
    """Дублирование товара"""
    try:
        original = self.get_product(shop_id, product_id)
        if not original:
            return None
        
        # Создание нового товара
        new_product = Product(
            shop_id=shop_id,
            name=new_name or f"{original.name} - Копия",
            description=original.description,
            price=original.price,
            original_price=original.original_price,
            category_id=original.category_id,
            stock_quantity=0,  # У нового товара запас 0
            sku=f"{original.sku}_КОПИЯ" if original.sku else None,
            status=ProductStatus.PENDING,  # Дублированный товар помечается как ожидающий
            is_featured=False,  # Дублированный товар не помечается как рекомендуемый
            is_new=True,  # Дублированный товар помечается как новый
            tags=original.tags.copy() if original.tags else [],
            attributes=original.attributes.copy() if original.attributes else {},
            meta_title=original.meta_title,
            meta_description=original.meta_description
        )
        
        self.db.add(new_product)
        self.db.flush()  # Получение ID нового товара
        
        # Копирование изображений (только ссылки, не файлы)
        for image in original.images:
            new_image = ProductImage(
                product_id=new_product.id,
                image_url=image.image_url,
                thumbnail_url=image.thumbnail_url,
                alt_text=image.alt_text,
                is_primary=image.is_primary,
                sort_order=image.sort_order
            )
            self.db.add(new_image)
        
        self.db.commit()
        self.db.refresh(new_product)
        
        logger.info(f"Дублирован товар {product_id} -> {new_product.id}")
        return new_product
        
    except Exception as e:
        self.db.rollback()
        logger.error(f"Ошибка при дублировании товара: {e}")
        raise


def search_products_full_text(
    self,
    shop_id: int,
    query: str,
    limit: int = 50
) -> List[Product]:
    """Полнотекстовый поиск товаров"""
    try:
        # Формирование условий поиска
        search_term = f"%{query}%"
        
        products = self.db.query(Product)\
            .options(joinedload(Product.images))\
            .filter(
                Product.shop_id == shop_id,
                Product.status == ProductStatus.ACTIVE,
                or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term),
                    Product.sku.ilike(search_term)
                )
            ).order_by(
                desc(Product.is_featured),
                desc(Product.created_at)
            ).limit(limit).all()
        
        return products
        
    except Exception as e:
        logger.error(f"Ошибка при полнотекстовом поиске товаров: {e}")
        return []