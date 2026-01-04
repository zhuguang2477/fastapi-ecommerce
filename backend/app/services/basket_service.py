# backend/app/services/basket_service.py
"""
Сервис корзины покупок
Обработка бизнес-логики, связанной с корзиной покупок
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging
import secrets

from backend.app.models.basket import Basket, BasketStatus
from backend.app.models.basket_item import BasketItem
from backend.app.models.customer import Customer
from backend.app.models.product import Product, ProductVariant
from backend.app.schemas.basket import (
    BasketCreate, BasketUpdate, BasketItemCreate, BasketItemUpdate,
    BasketResponse, BasketItemResponse, BasketList
)

logger = logging.getLogger(__name__)


class BasketService:
    """Сервис корзины покупок"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_basket_token(self) -> str:
        """Сгенерировать токен корзины"""
        return f"basket_{secrets.token_hex(16)}_{int(datetime.utcnow().timestamp())}"
    
    def get_basket(self, shop_id: int, basket_id: int, include_items: bool = True) -> Optional[Basket]:
        """Получить отдельную корзину"""
        try:
            query = self.db.query(Basket).filter(
                Basket.id == basket_id,
                Basket.shop_id == shop_id
            )
            
            if include_items:
                query = query.options(joinedload(Basket.items))
            
            return query.first()
        except Exception as e:
            logger.error(f"Ошибка получения корзины: {e}")
            return None
    
    def get_basket_by_token(self, shop_id: int, basket_token: str, include_items: bool = True) -> Optional[Basket]:
        """Получить корзину по токену"""
        try:
            query = self.db.query(Basket).filter(
                Basket.basket_token == basket_token,
                Basket.shop_id == shop_id
            )
            
            if include_items:
                query = query.options(joinedload(Basket.items))
            
            return query.first()
        except Exception as e:
            logger.error(f"Ошибка получения корзины по токену: {e}")
            return None
    
    def get_customer_basket(self, shop_id: int, customer_id: int, create_if_not_exists: bool = True) -> Optional[Basket]:
        """Получить корзину клиента"""
        try:
            basket = self.db.query(Basket)\
                .options(joinedload(Basket.items))\
                .filter(
                    Basket.shop_id == shop_id,
                    Basket.customer_id == customer_id,
                    Basket.status == BasketStatus.ACTIVE.value
                )\
                .order_by(desc(Basket.created_at))\
                .first()
            
            if not basket and create_if_not_exists:
                # Создать новую корзину
                basket_data = BasketCreate(
                    basket_token=self.generate_basket_token(),
                    status=BasketStatus.ACTIVE.value,
                    is_guest=False,
                    currency="RUB",
                    expires_at=datetime.utcnow() + timedelta(days=30)
                )
                
                basket = self.create_basket(shop_id, customer_id, basket_data)
            
            return basket
        except Exception as e:
            logger.error(f"Ошибка получения корзины клиента: {e}")
            return None
    
    def get_guest_basket(self, shop_id: int, session_id: str, create_if_not_exists: bool = True) -> Optional[Basket]:
        """Получить корзину гостя"""
        try:
            basket = self.db.query(Basket)\
                .options(joinedload(Basket.items))\
                .filter(
                    Basket.shop_id == shop_id,
                    Basket.session_id == session_id,
                    Basket.is_guest == True,
                    Basket.status == BasketStatus.ACTIVE.value
                )\
                .order_by(desc(Basket.created_at))\
                .first()
            
            if not basket and create_if_not_exists:
                # Создать новую корзину гостя
                basket_data = BasketCreate(
                    basket_token=self.generate_basket_token(),
                    session_id=session_id,
                    status=BasketStatus.ACTIVE.value,
                    is_guest=True,
                    currency="RUB",
                    expires_at=datetime.utcnow() + timedelta(days=7)
                )
                
                basket = self.create_guest_basket(shop_id, basket_data)
            
            return basket
        except Exception as e:
            logger.error(f"Ошибка получения корзины гостя: {e}")
            return None
    
    def create_basket(self, shop_id: int, customer_id: int, data: BasketCreate) -> Optional[Basket]:
        """Создать корзину"""
        try:
            # Проверить существование клиента
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id,
                Customer.shop_id == shop_id
            ).first()
            
            if not customer:
                logger.error(f"Клиент не существует: customer_id={customer_id}, shop_id={shop_id}")
                return None
            
            basket = Basket(
                shop_id=shop_id,
                customer_id=customer_id,
                **data.dict(exclude={'shop_id', 'customer_id'})
            )
            
            self.db.add(basket)
            self.db.commit()
            self.db.refresh(basket)
            
            logger.info(f"Корзина успешно создана: id={basket.id}, customer_id={customer_id}")
            return basket
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка создания корзины: {e}")
            return None
    
    def create_guest_basket(self, shop_id: int, data: BasketCreate) -> Optional[Basket]:
        """Создать корзину гостя"""
        try:
            basket = Basket(
                shop_id=shop_id,
                **data.dict(exclude={'shop_id'})
            )
            
            self.db.add(basket)
            self.db.commit()
            self.db.refresh(basket)
            
            logger.info(f"Корзина гостя успешно создана: id={basket.id}, session_id={data.session_id}")
            return basket
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка создания корзины гостя: {e}")
            return None
    
    def update_basket(self, shop_id: int, basket_id: int, data: BasketUpdate) -> Optional[Basket]:
        """Обновить корзину"""
        try:
            basket = self.get_basket(shop_id, basket_id, include_items=False)
            if not basket:
                return None
            
            update_data = data.dict(exclude_unset=True)
            
            # Обновить поля
            for field, value in update_data.items():
                if hasattr(basket, field):
                    setattr(basket, field, value)
            
            # Если статус изменился на конвертированный, обновить время последней активности
            if 'status' in update_data and update_data['status'] == BasketStatus.CONVERTED.value:
                basket.last_activity_at = datetime.utcnow()
            
            basket.updated_at = datetime.utcnow()
            
            # Пересчитать общую сумму
            self._recalculate_basket_totals(basket)
            
            self.db.commit()
            self.db.refresh(basket)
            
            logger.info(f"Корзина успешно обновлена: id={basket.id}")
            return basket
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка обновления корзины: {e}")
            return None
    
    def _recalculate_basket_totals(self, basket: Basket):
        """Пересчитать общую сумму корзины"""
        if not basket.items:
            basket.subtotal = 0.0
            basket.discount_amount = 0.0
            basket.shipping_amount = 0.0
            basket.tax_amount = 0.0
            basket.total_amount = 0.0
            basket.item_count = 0
            basket.unique_item_count = 0
            return
        
        # Рассчитать промежуточную сумму
        subtotal = sum(item.unit_price * item.quantity for item in basket.items)
        
        # Применить скидку
        discount_amount = sum(item.discount_amount * item.quantity for item in basket.items)
        
        # Рассчитать окончательную сумму
        final_subtotal = subtotal - discount_amount
        
        # Рассчитать налог (предположим 10% налог)
        tax_rate = 0.10
        tax_amount = final_subtotal * tax_rate
        
        # Рассчитать стоимость доставки (в зависимости от стратегии)
        shipping_amount = self._calculate_shipping(basket, final_subtotal)
        
        # Рассчитать общую сумму
        total_amount = final_subtotal + tax_amount + shipping_amount
        
        # Обновить корзину
        basket.subtotal = float(subtotal)
        basket.discount_amount = float(discount_amount)
        basket.shipping_amount = float(shipping_amount)
        basket.tax_amount = float(tax_amount)
        basket.total_amount = float(total_amount)
        basket.item_count = sum(item.quantity for item in basket.items)
        basket.unique_item_count = len(basket.items)
    
    def _calculate_shipping(self, basket: Basket, subtotal: float) -> float:
        """Рассчитать стоимость доставки"""
        # Порог бесплатной доставки
        free_shipping_threshold = 5000.0
        
        if subtotal >= free_shipping_threshold:
            return 0.0
        
        # Базовая стоимость доставки
        base_shipping = 300.0
        
        # Рассчитать дополнительную стоимость доставки в зависимости от веса товара
        weight_shipping = 0.0
        for item in basket.items:
            if item.weight and item.weight > 1.0:
                weight_shipping += (item.weight - 1.0) * 100.0
        
        return float(base_shipping + weight_shipping)
    
    def delete_basket(self, shop_id: int, basket_id: int) -> bool:
        """Удалить корзину"""
        try:
            basket = self.get_basket(shop_id, basket_id, include_items=False)
            if not basket:
                return False
            
            self.db.delete(basket)
            self.db.commit()
            
            logger.info(f"Корзина успешно удалена: id={basket_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка удаления корзины: {e}")
            return False
    
    def add_item_to_basket(
        self, 
        shop_id: int, 
        basket_id: int, 
        item_data: BasketItemCreate
    ) -> Optional[BasketItem]:
        """Добавить товар в корзину"""
        try:
            basket = self.get_basket(shop_id, basket_id, include_items=True)
            if not basket:
                return None
            
            # Проверить существование товара
            product = self.db.query(Product).filter(
                Product.id == item_data.product_id,
                Product.shop_id == shop_id
            ).first()
            
            if not product:
                logger.error(f"Товар не существует: product_id={item_data.product_id}, shop_id={shop_id}")
                return None
            
            # Проверить варианты товара
            variant = None
            if item_data.variant_id:
                variant = self.db.query(ProductVariant).filter(
                    ProductVariant.id == item_data.variant_id,
                    ProductVariant.product_id == product.id
                ).first()
                
                if not variant:
                    logger.error(f"Вариант товара не существует: variant_id={item_data.variant_id}")
                    return None
            
            # Проверить наличие на складе
            if product.manage_stock:
                available_stock = variant.stock_quantity if variant else product.stock_quantity
                if available_stock is not None and available_stock < item_data.quantity:
                    logger.warning(f"Недостаточно товара на складе: product_id={product.id}, наличие={available_stock}, запрошено={item_data.quantity}")
                    return None
            
            # Проверить, существует ли уже такой товар
            existing_item = None
            for item in basket.items:
                if item.product_id == item_data.product_id and item.variant_id == item_data.variant_id:
                    existing_item = item
                    break
            
            if existing_item:
                # Обновить количество существующего товара
                new_quantity = existing_item.quantity + item_data.quantity
                
                # Снова проверить наличие на складе
                if product.manage_stock:
                    available_stock = variant.stock_quantity if variant else product.stock_quantity
                    if available_stock is not None and available_stock < new_quantity:
                        logger.warning(f"Недостаточно товара на складе после обновления: product_id={product.id}, наличие={available_stock}, новое количество={new_quantity}")
                        return None
                
                existing_item.quantity = new_quantity
                existing_item.updated_at = datetime.utcnow()
                basket_item = existing_item
            else:
                # Создать новый товар
                basket_item = BasketItem(
                    basket_id=basket_id,
                    product_name=product.name,
                    product_sku=variant.sku if variant else product.sku,
                    variant_name=variant.name if variant else None,
                    variant_attributes=variant.attributes if variant else None,
                    unit_price=variant.price if variant else product.price,
                    original_price=variant.original_price if variant else product.original_price,
                    product_image_url=product.images[0].image_url if product.images else None,
                    product_slug=product.slug,
                    is_in_stock=(not product.manage_stock) or 
                               ((variant.stock_quantity if variant else product.stock_quantity) or 0) > 0,
                    stock_quantity=variant.stock_quantity if variant else product.stock_quantity,
                    requires_shipping=product.requires_shipping,
                    weight=variant.weight if variant else product.weight,
                    dimensions=variant.dimensions if variant else product.dimensions,
                    **item_data.dict()
                )
                
                # Рассчитать скидку
                if basket_item.original_price and basket_item.original_price > basket_item.unit_price:
                    basket_item.discount_amount = basket_item.original_price - basket_item.unit_price
                    basket_item.discount_percentage = (basket_item.discount_amount / basket_item.original_price) * 100
                else:
                    basket_item.discount_amount = 0.0
                    basket_item.discount_percentage = 0.0
                
                basket.items.append(basket_item)
            
            # Пересчитать общую сумму корзины
            self._recalculate_basket_totals(basket)
            basket.last_activity_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(basket_item)
            
            logger.info(f"Товар успешно добавлен в корзину: basket_id={basket_id}, product_id={item_data.product_id}")
            return basket_item
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка добавления товара в корзину: {e}")
            return None
    
    def update_basket_item(
        self, 
        shop_id: int, 
        basket_id: int, 
        item_id: int, 
        item_data: BasketItemUpdate
    ) -> Optional[BasketItem]:
        """Обновить товар в корзине"""
        try:
            basket = self.get_basket(shop_id, basket_id, include_items=True)
            if not basket:
                return None
            
            # Найти товар
            basket_item = None
            for item in basket.items:
                if item.id == item_id:
                    basket_item = item
                    break
            
            if not basket_item:
                return None
            
            update_data = item_data.dict(exclude_unset=True)
            
            # Если обновляется количество, проверить наличие на складе
            if 'quantity' in update_data:
                product = self.db.query(Product).filter(
                    Product.id == basket_item.product_id,
                    Product.shop_id == shop_id
                ).first()
                
                if product and product.manage_stock:
                    available_stock = product.stock_quantity
                    if available_stock is not None and available_stock < update_data['quantity']:
                        logger.warning(f"Недостаточно товара на складе: product_id={product.id}, наличие={available_stock}, запрошено={update_data['quantity']}")
                        return None
            
            # Обновить поля
            for field, value in update_data.items():
                if hasattr(basket_item, field):
                    setattr(basket_item, field, value)
            
            basket_item.updated_at = datetime.utcnow()
            
            # Пересчитать общую сумму корзины
            self._recalculate_basket_totals(basket)
            basket.last_activity_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(basket_item)
            
            logger.info(f"Товар в корзине успешно обновлен: item_id={item_id}")
            return basket_item
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка обновления товара в корзине: {e}")
            return None
    
    def remove_item_from_basket(self, shop_id: int, basket_id: int, item_id: int) -> bool:
        """Удалить товар из корзины"""
        try:
            basket = self.get_basket(shop_id, basket_id, include_items=True)
            if not basket:
                return False
            
            # Найти товар
            basket_item = None
            for item in basket.items:
                if item.id == item_id:
                    basket_item = item
                    break
            
            if not basket_item:
                return False
            
            basket.items.remove(basket_item)
            
            # Пересчитать общую сумму корзины
            self._recalculate_basket_totals(basket)
            basket.last_activity_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Товар успешно удален из корзины: basket_id={basket_id}, item_id={item_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка удаления товара из корзины: {e}")
            return False
    
    def clear_basket(self, shop_id: int, basket_id: int) -> bool:
        """Очистить корзину"""
        try:
            basket = self.get_basket(shop_id, basket_id, include_items=True)
            if not basket:
                return False
            
            basket.items.clear()
            self._recalculate_basket_totals(basket)
            basket.last_activity_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Корзина успешно очищена: basket_id={basket_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка очистки корзины: {e}")
            return False
    
    def convert_guest_to_customer_basket(self, shop_id: int, guest_basket_token: str, customer_id: int) -> Optional[Basket]:
        """Конвертировать корзину гостя в корзину клиента"""
        try:
            # Получить корзину гостя
            guest_basket = self.get_basket_by_token(shop_id, guest_basket_token, include_items=True)
            if not guest_basket or not guest_basket.is_guest:
                return None
            
            # Получить существующую корзину клиента
            customer_basket = self.get_customer_basket(shop_id, customer_id, create_if_not_exists=False)
            
            if customer_basket:
                # Объединить корзины
                self.merge_baskets(guest_basket.id, customer_basket.id)
                return customer_basket
            else:
                # Непосредственно конвертировать корзину гостя в корзину клиента
                guest_basket.is_guest = False
                guest_basket.customer_id = customer_id
                guest_basket.session_id = None
                guest_basket.updated_at = datetime.utcnow()
                
                self.db.commit()
                self.db.refresh(guest_basket)
                
                logger.info(f"Корзина гостя успешно конвертирована в корзину клиента: basket_id={guest_basket.id}, customer_id={customer_id}")
                return guest_basket
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка конвертации корзины гостя: {e}")
            return None
    
    def merge_baskets(self, source_basket_id: int, target_basket_id: int) -> bool:
        """Объединить корзины"""
        try:
            source_basket = self.get_basket_by_id(source_basket_id, include_items=True)
            target_basket = self.get_basket_by_id(target_basket_id, include_items=True)
            
            if not source_basket or not target_basket:
                return False
            
            # Объединить товары
            for source_item in source_basket.items:
                # Проверить, есть ли уже такой товар в целевой корзине
                existing_item = None
                for target_item in target_basket.items:
                    if (target_item.product_id == source_item.product_id and 
                        target_item.variant_id == source_item.variant_id):
                        existing_item = target_item
                        break
                
                if existing_item:
                    # Объединить количество
                    existing_item.quantity += source_item.quantity
                    existing_item.updated_at = datetime.utcnow()
                else:
                    # Создать новый товар
                    new_item = BasketItem(
                        basket_id=target_basket_id,
                        product_id=source_item.product_id,
                        variant_id=source_item.variant_id,
                        product_name=source_item.product_name,
                        product_sku=source_item.product_sku,
                        variant_name=source_item.variant_name,
                        variant_attributes=source_item.variant_attributes,
                        unit_price=source_item.unit_price,
                        original_price=source_item.original_price,
                        discount_amount=source_item.discount_amount,
                        quantity=source_item.quantity,
                        max_quantity=source_item.max_quantity,
                        product_image_url=source_item.product_image_url,
                        product_slug=source_item.product_slug,
                        is_in_stock=source_item.is_in_stock,
                        stock_quantity=source_item.stock_quantity,
                        requires_shipping=source_item.requires_shipping,
                        weight=source_item.weight,
                        dimensions=source_item.dimensions,
                        discount_percentage=source_item.discount_percentage,
                        discount_reason=source_item.discount_reason,
                        added_at=source_item.added_at
                    )
                    target_basket.items.append(new_item)
            
            # Пересчитать общую сумму целевой корзины
            self._recalculate_basket_totals(target_basket)
            target_basket.last_activity_at = datetime.utcnow()
            
            # Пометить исходную корзину как объединенную
            source_basket.status = BasketStatus.CONVERTED.value
            source_basket.last_activity_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Корзины успешно объединены: source={source_basket_id}, target={target_basket_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка объединения корзин: {e}")
            return False
    
    def get_basket_by_id(self, basket_id: int, include_items: bool = True) -> Optional[Basket]:
        """Получить корзину по ID (внутренний метод)"""
        try:
            query = self.db.query(Basket).filter(Basket.id == basket_id)
            
            if include_items:
                query = query.options(joinedload(Basket.items))
            
            return query.first()
        except Exception as e:
            logger.error(f"Ошибка получения корзины по ID: {e}")
            return None
    
    def abandon_old_baskets(self, days_threshold: int = 30):
        """Пометить старые заброшенные корзины"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
            
            abandoned_count = self.db.query(Basket).filter(
                Basket.status == BasketStatus.ACTIVE.value,
                Basket.last_activity_at < cutoff_date
            ).update({
                "status": BasketStatus.ABANDONED.value,
                "updated_at": datetime.utcnow()
            })
            
            self.db.commit()
            
            logger.info(f"Заброшенные корзины успешно помечены: количество={abandoned_count}")
            return abandoned_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка пометки заброшенных корзин: {e}")
            return 0
    
    def get_baskets(
        self,
        shop_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        is_guest: Optional[bool] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None
    ) -> Tuple[List[Basket], int]:
        """Получить список корзин"""
        try:
            query = self.db.query(Basket).filter(Basket.shop_id == shop_id)
            
            # Применить фильтры
            if status:
                query = query.filter(Basket.status == status)
            if customer_id:
                query = query.filter(Basket.customer_id == customer_id)
            if is_guest is not None:
                query = query.filter(Basket.is_guest == is_guest)
            if created_after:
                query = query.filter(Basket.created_at >= created_after)
            if created_before:
                query = query.filter(Basket.created_at <= created_before)
            
            # Получить общее количество
            total = query.count()
            
            # Применить сортировку и пагинацию
            baskets = query.order_by(desc(Basket.created_at))\
                          .offset(skip)\
                          .limit(limit)\
                          .all()
            
            return baskets, total
            
        except Exception as e:
            logger.error(f"Ошибка получения списка корзин: {e}")
            raise