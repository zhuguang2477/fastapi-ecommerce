# backend/app/services/order_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_, extract, asc
from math import ceil
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
import uuid
import logging

from backend.app.models.order import Order, OrderItem
from backend.app.models.product import Product
from backend.app.models.shop import Shop
from backend.app.schemas.order import OrderCreate, OrderUpdate, OrderStatus, PaymentStatus  

try:
    from backend.app.schemas.order import OrderSearch, OrderBulkUpdate, OrderExportRequest
except ImportError:
    # Если импорт не удался, создаем простые классы-заменители
    class OrderSearch:
        pass
    
    class OrderBulkUpdate:
        pass
    
    class OrderExportRequest:
        pass


logger = logging.getLogger(__name__)

class OrderService:
    """Класс сервиса для работы с заказами"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_order_number(self) -> str:
        """Генерирует номер заказа"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4().int)[:8]
        return f"ORD{timestamp}{unique_id}"
    
    def create_order(self, shop_id: int, order_data: OrderCreate) -> Order:
        """Создает новый заказ"""
        try:
            # Генерируем номер заказа
            order_number = self.generate_order_number()
            
            # Рассчитываем общую стоимость товаров
            subtotal = 0
            order_items = []
            
            for item_data in order_data.items:
                # Получаем информацию о товаре
                product = self.db.query(Product).filter(
                    Product.id == item_data.product_id,
                    Product.shop_id == shop_id,
                    Product.status == "active"
                ).first()
                
                if not product:
                    raise ValueError(f"Товар не найден или снят с продажи: {item_data.product_id}")
                
                if product.stock_quantity < item_data.quantity:
                    raise ValueError(f"Недостаточно товара на складе: {product.name}")
                
                # Рассчитываем общую стоимость товара
                item_total = item_data.unit_price * item_data.quantity
                subtotal += item_total
                
                # Создаем позицию заказа
                order_item = OrderItem(
                    product_id=product.id,
                    product_name=item_data.product_name,
                    unit_price=item_data.unit_price,
                    quantity=item_data.quantity,
                    total_price=item_total,
                    product_data={
                        "product_id": product.id,
                        "name": product.name,
                        "price": product.price,
                        "image_url": product.images[0].image_url if product.images else None
                    }
                )
                order_items.append(order_item)
            
            # Рассчитываем итоговую сумму (с доставкой, налогами, скидкой)
            shipping_amount = 0  # Стоимость доставки, можно рассчитать позже
            tax_amount = subtotal * 0.1  # Налог 10%, пример
            discount_amount = 0  # Скидка, пример
            total_amount = subtotal + shipping_amount + tax_amount - discount_amount
            
            # Создаем заказ
            order = Order(
                shop_id=shop_id,
                order_number=order_number,
                customer_email=order_data.customer_email,
                customer_name=order_data.customer_name,
                customer_phone=order_data.customer_phone,
                shipping_address=order_data.shipping_address,
                billing_address=order_data.billing_address,
                customer_notes=order_data.customer_notes,
                subtotal=subtotal,
                shipping_amount=shipping_amount,
                tax_amount=tax_amount,
                discount_amount=discount_amount,
                total_amount=total_amount,
                payment_method=order_data.payment_method.value if order_data.payment_method else None,
                items=order_items
            )
            
            self.db.add(order)
            self.db.flush()  # Получаем order.id, но не фиксируем транзакцию
            
            # Обновляем количество товаров на складе
            for item_data in order_data.items:
                product = self.db.query(Product).filter(
                    Product.id == item_data.product_id
                ).first()
                if product:
                    product.stock_quantity -= item_data.quantity
            
            self.db.commit()
            self.db.refresh(order)
            
            logger.info(f"Заказ успешно создан: {order_number}")
            return order
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при создании заказа: {e}")
            raise
    
    def get_order(self, shop_id: int, order_id: int) -> Optional[Order]:
        """Получает один заказ"""
        return self.db.query(Order).filter(
            Order.id == order_id,
            Order.shop_id == shop_id
        ).first()
    
    def get_orders(
        self,
        shop_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        customer_email: Optional[str] = None
    ) -> Tuple[List[Order], int]:
        """Получает список заказов"""
        query = self.db.query(Order).filter(Order.shop_id == shop_id)
        
        # Применяем фильтры
        if status:
            query = query.filter(Order.status == status)
        
        if customer_email:
            query = query.filter(Order.customer_email.ilike(f"%{customer_email}%"))
        
        if start_date:
            query = query.filter(Order.created_at >= start_date)
        
        if end_date:
            query = query.filter(Order.created_at <= end_date)
        
        # Получаем общее количество
        total = query.count()
        
        # Применяем пагинацию и сортировку
        orders = query.order_by(desc(Order.created_at)) \
                     .offset(skip) \
                     .limit(limit) \
                     .all()
        
        return orders, total
    
    def update_order(
        self,
        shop_id: int,
        order_id: int,
        update_data: OrderUpdate
    ) -> Optional[Order]:
        """Обновляет заказ"""
        order = self.get_order(shop_id, order_id)
        if not order:
            return None
        
        try:
            update_dict = update_data.dict(exclude_unset=True)
            
            # Особый обработчик изменения статуса
            if 'status' in update_dict:
                new_status = update_dict['status']
                old_status = order.status
                
                # Записываем время отправки
                if new_status == OrderStatus.SHIPPED and old_status != OrderStatus.SHIPPED:
                    order.shipped_at = datetime.utcnow()
                
                # Записываем время оплаты
                if new_status == OrderStatus.PAID and old_status != OrderStatus.PAID:
                    order.paid_at = datetime.utcnow()
                    order.payment_status = "paid"
            
            # Обновляем поля заказа
            for field, value in update_dict.items():
                setattr(order, field, value)
            
            order.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(order)
            
            logger.info(f"Заказ успешно обновлен: {order.order_number}")
            return order
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при обновлении заказа: {e}")
            raise
    
    def delete_order(self, shop_id: int, order_id: int) -> bool:
        """Удаляет заказ (мягкое удаление)"""
        order = self.get_order(shop_id, order_id)
        if not order:
            return False
        
        try:
            # Мягкое удаление: меняем статус на отмененный
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.utcnow()
            
            # Восстанавливаем количество товаров на складе
            for item in order.items:
                product = self.db.query(Product).filter(
                    Product.id == item.product_id
                ).first()
                if product:
                    product.stock_quantity += item.quantity
            
            self.db.commit()
            logger.info(f"Заказ отменен: {order.order_number}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при удалении заказа: {e}")
            return False
    
    def get_order_stats(self, shop_id: int) -> Dict[str, Any]:
        """Получает статистику по заказам"""
        # Общее количество заказов
        total_orders = self.db.query(func.count(Order.id)).filter(
            Order.shop_id == shop_id
        ).scalar() or 0
        
        # Общий доход
        total_revenue = self.db.query(func.sum(Order.total_amount)).filter(
            Order.shop_id == shop_id,
            Order.status.in_([OrderStatus.PAID, OrderStatus.DELIVERED])
        ).scalar() or 0
        
        # Средняя стоимость заказа
        avg_order_value = self.db.query(func.avg(Order.total_amount)).filter(
            Order.shop_id == shop_id,
            Order.status.in_([OrderStatus.PAID, OrderStatus.DELIVERED])
        ).scalar() or 0
        
        # Количество заказов по статусам
        status_counts = {}
        for status in OrderStatus:
            count = self.db.query(func.count(Order.id)).filter(
                Order.shop_id == shop_id,
                Order.status == status
            ).scalar() or 0
            status_counts[status] = count
        
        return {
            "total_orders": total_orders,
            "total_revenue": float(total_revenue),
            "average_order_value": float(avg_order_value),
            "status_counts": status_counts
        }
    
    def get_daily_stats(
        self,
        shop_id: int,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Получает ежедневную статистику по заказам"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Используем SQL для извлечения даты и группировки
        results = self.db.query(
            func.date(Order.created_at).label('date'),
            func.count(Order.id).label('order_count'),
            func.sum(Order.total_amount).label('daily_revenue')
        ).filter(
            Order.shop_id == shop_id,
            Order.created_at >= start_date,
            Order.created_at <= end_date
        ).group_by(func.date(Order.created_at)) \
         .order_by(func.date(Order.created_at)) \
         .all()
        
        daily_stats = []
        for result in results:
            daily_stats.append({
                "date": result.date.isoformat() if result.date else None,
                "orders_count": result.order_count or 0,
                "total_revenue": float(result.daily_revenue or 0)
            })
    
    # Добавляем следующие методы в backend/app/services/order_service.py

def search_orders(
    self,
    shop_id: int,
    search_params: OrderSearch,
    skip: int = 0,
    limit: int = 100,
    include_items: bool = False
) -> Tuple[List[Order], int, Dict[str, Any]]:
    """Поиск заказов (поддерживает сложную фильтрацию и поиск)"""
    try:
        query = self.db.query(Order).filter(Order.shop_id == shop_id)
        
        # Применяем условия поиска
        if search_params.query:
            search_term = f"%{search_params.query}%"
            query = query.filter(
                or_(
                    Order.order_number.ilike(search_term),
                    Order.customer_email.ilike(search_term),
                    Order.customer_name.ilike(search_term),
                    Order.customer_phone.ilike(search_term),
                    Order.admin_notes.ilike(search_term),
                    Order.tracking_number.ilike(search_term)
                )
            )
        
        # Применяем условия фильтрации
        if search_params.filter:
            filter_data = search_params.filter.dict(exclude_unset=True)
            
            if filter_data.get('status'):
                query = query.filter(Order.status == filter_data['status'])
            
            if filter_data.get('payment_status'):
                query = query.filter(Order.payment_status == filter_data['payment_status'])
            
            if filter_data.get('payment_method'):
                query = query.filter(Order.payment_method == filter_data['payment_method'])
            
            if filter_data.get('customer_email'):
                query = query.filter(Order.customer_email.ilike(f"%{filter_data['customer_email']}%"))
            
            if filter_data.get('customer_phone'):
                query = query.filter(Order.customer_phone.ilike(f"%{filter_data['customer_phone']}%"))
            
            if filter_data.get('order_number'):
                query = query.filter(Order.order_number.ilike(f"%{filter_data['order_number']}%"))
            
            if filter_data.get('min_amount'):
                query = query.filter(Order.total_amount >= filter_data['min_amount'])
            
            if filter_data.get('max_amount'):
                query = query.filter(Order.total_amount <= filter_data['max_amount'])
            
            if filter_data.get('start_date'):
                query = query.filter(Order.created_at >= filter_data['start_date'])
            
            if filter_data.get('end_date'):
                query = query.filter(Order.created_at <= filter_data['end_date'])
            
            if filter_data.get('has_customer_notes') is not None:
                if filter_data['has_customer_notes']:
                    query = query.filter(Order.customer_notes.isnot(None))
                else:
                    query = query.filter(Order.customer_notes.is_(None))
        
        # Получаем общее количество
        total = query.count()
        
        # Применяем сортировку
        sort_field = search_params.sort_by
        sort_order = search_params.sort_order
        
        # Сопоставление поддерживаемых полей сортировки
        sort_mapping = {
            "order_number": Order.order_number,
            "customer_email": Order.customer_email,
            "customer_name": Order.customer_name,
            "total_amount": Order.total_amount,
            "status": Order.status,
            "payment_status": Order.payment_status,
            "created_at": Order.created_at,
            "updated_at": Order.updated_at,
            "paid_at": Order.paid_at,
            "shipped_at": Order.shipped_at
        }
        
        order_by_field = sort_mapping.get(sort_field, Order.created_at)
        
        if sort_order == "desc":
            order_by_field = desc(order_by_field)
        else:
            order_by_field = asc(order_by_field)
        
        # Применяем пагинацию
        query = query.order_by(order_by_field)
        
        if include_items:
            query = query.options(joinedload(Order.items))
        
        orders = query.offset(skip).limit(limit).all()
        
        # Рассчитываем информацию о пагинации
        total_pages = ceil(total / limit) if limit > 0 else 1
        current_page = (skip // limit) + 1 if limit > 0 else 1
        
        pagination_info = {
            "total": total,
            "page": current_page,
            "page_size": limit,
            "total_pages": total_pages,
            "has_next": skip + limit < total,
            "has_previous": skip > 0
        }
        
        return orders, total, pagination_info
        
    except Exception as e:
        logger.error(f"Ошибка при поиске заказов: {e}")
        raise


def bulk_update_orders(
    self,
    shop_id: int,
    update_data: OrderBulkUpdate
) -> Dict[str, Any]:
    """Массовое обновление заказов"""
    try:
        # Проверяем, что все заказы принадлежат этому магазину
        valid_orders = self.db.query(Order).filter(
            Order.id.in_(update_data.order_ids),
            Order.shop_id == shop_id
        ).all()
        
        if len(valid_orders) != len(update_data.order_ids):
            invalid_ids = set(update_data.order_ids) - {order.id for order in valid_orders}
            raise ValueError(f"Некоторые заказы не существуют или не принадлежат этому магазину: {list(invalid_ids)}")
        
        update_count = 0
        updated_orders = []
        
        # Подготавливаем данные для обновления
        update_dict = update_data.dict(exclude_unset=True, exclude={'order_ids'})
        
        for order in valid_orders:
            # Записываем изменение статуса
            old_status = order.status
            new_status = update_dict.get('status')
            
            if new_status and new_status != old_status:
                # Записываем историю изменения статусов
                status_history = {
                    'old_status': old_status,
                    'new_status': new_status,
                    'changed_at': datetime.utcnow(),
                    'notes': update_dict.get('admin_notes', 'Массовое обновление')
                }
                
                if not order.status_history:
                    order.status_history = [status_history]
                else:
                    order.status_history.append(status_history)
                
                # Записываем время отправки
                if new_status == OrderStatus.SHIPPED and old_status != OrderStatus.SHIPPED:
                    order.shipped_at = datetime.utcnow()
                
                # Записываем время оплаты
                if new_status == OrderStatus.PAID and old_status != OrderStatus.PAID:
                    order.paid_at = datetime.utcnow()
                    order.payment_status = PaymentStatus.PAID
            
            # Обновляем поля заказа
            for field, value in update_dict.items():
                if hasattr(order, field):
                    setattr(order, field, value)
            
            order.updated_at = datetime.utcnow()
            updated_orders.append({
                'id': order.id,
                'order_number': order.order_number,
                'status': order.status,
                'updated_at': order.updated_at
            })
            update_count += 1
        
        self.db.commit()
        
        logger.info(f"Массово обновлено {update_count} заказов")
        
        return {
            'success': True,
            'updated_count': update_count,
            'updated_orders': updated_orders
        }
        
    except Exception as e:
        self.db.rollback()
        logger.error(f"Ошибка при массовом обновлении заказов: {e}")
        raise


def export_orders(
    self,
    shop_id: int,
    export_params: OrderExportRequest
) -> Dict[str, Any]:
    """Экспортирует данные заказов"""
    try:
        # Строим запрос
        query = self.db.query(Order).filter(Order.shop_id == shop_id)
        
        # Применяем условия фильтрации
        if export_params.filter:
            filter_data = export_params.filter.dict(exclude_unset=True)
            
            for field, value in filter_data.items():
                if hasattr(Order, field) and value is not None:
                    column = getattr(Order, field)
                    
                    if isinstance(value, str) and field in ['customer_email', 'customer_name', 'customer_phone']:
                        query = query.filter(column.ilike(f"%{value}%"))
                    elif field in ['start_date', 'end_date']:
                        # Эти поля требуют специальной обработки
                        continue
                    elif field == 'min_amount':
                        query = query.filter(Order.total_amount >= value)
                    elif field == 'max_amount':
                        query = query.filter(Order.total_amount <= value)
                    elif field == 'has_customer_notes':
                        if value:
                            query = query.filter(Order.customer_notes.isnot(None))
                        else:
                            query = query.filter(Order.customer_notes.is_(None))
                    else:
                        query = query.filter(column == value)
        
        # Выполняем запрос
        orders = query.order_by(desc(Order.created_at)).all()
        
        # Подготавливаем данные
        export_data = []
        for order in orders:
            order_data = {}
            
            for column in export_params.columns:
                if hasattr(order, column):
                    value = getattr(order, column)
                    
                    # Обрабатываем специальные поля
                    if column == 'shipping_address' or column == 'billing_address':
                        if value:
                            # Форматируем адрес
                            address = value
                            value = f"{address.get('address_line1', '')} {address.get('address_line2', '')}, {address.get('city', '')}, {address.get('state', '')} {address.get('postal_code', '')}"
                        else:
                            value = ""
                    
                    # Обрабатываем поля с датами
                    elif isinstance(value, datetime):
                        value = value.strftime("%Y-%m-%d %H:%M:%S")
                    
                    order_data[column] = value
            
            export_data.append(order_data)
        
        # Генерируем имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"orders_export_{shop_id}_{timestamp}"
        
        return {
            'data': export_data,
            'total_count': len(export_data),
            'filename': filename,
            'format': export_params.format
        }
        
    except Exception as e:
        logger.error(f"Ошибка при экспорте заказов: {e}")
        raise
    
        return daily_stats