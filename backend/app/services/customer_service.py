# backend/app/services/customer_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_, distinct, case, text, asc
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging

from backend.app.models.order import Order
from backend.app.models.customer import Customer
from backend.app.schemas.customer import (
    CustomerResponse, CustomerList, CustomerDetail, 
    CustomerStats, CustomerFilter, CustomerSearch, 
    CustomerStatus, CustomerType
)

logger = logging.getLogger(__name__)

class CustomerService:
    """Сервисный класс для работы с клиентами"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_customers_from_orders(self, shop_id: int) -> List[Dict[str, Any]]:
        """Агрегация информации о клиентах из данных заказов"""
        try:
            # Запрос всех заказов магазина с группировкой по email клиента
            results = self.db.query(
                Order.customer_email,
                func.max(Order.customer_name).label('name'),
                func.max(Order.customer_phone).label('phone'),
                func.count(Order.id).label('order_count'),
                func.sum(Order.total_amount).label('total_spent'),
                func.avg(Order.total_amount).label('avg_order_value'),
                func.min(Order.created_at).label('first_order_date'),
                func.max(Order.created_at).label('last_order_date'),
                func.array_agg(Order.status.distinct()).label('order_statuses')
            ).filter(
                Order.shop_id == shop_id,
                Order.customer_email.isnot(None)
            ).group_by(
                Order.customer_email
            ).order_by(
                desc(func.max(Order.created_at))
            ).all()
            
            customers = []
            for result in results:
                # Расчет статуса клиента
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                customer_status = "active" if result.last_order_date > thirty_days_ago else "inactive"
                
                # Определение типа клиента
                if result.first_order_date > thirty_days_ago:
                    customer_type = "new"
                elif result.order_count > 10 or result.total_spent > 5000:
                    customer_type = "vip"
                else:
                    customer_type = "regular"
                
                customers.append({
                    "email": result.customer_email,
                    "name": result.name,
                    "phone": result.phone,
                    "order_count": result.order_count,
                    "total_spent": float(result.total_spent or 0),
                    "avg_order_value": float(result.avg_order_value or 0),
                    "first_order_date": result.first_order_date,
                    "last_order_date": result.last_order_date,
                    "status": customer_status,
                    "type": customer_type,
                    "order_statuses": result.order_statuses or []
                })
            
            return customers
            
        except Exception as e:
            logger.error(f"Ошибка агрегации данных клиентов из заказов: {e}")
            raise
    
    def get_customers(
        self,
        shop_id: int,
        skip: int = 0,
        limit: int = 100,
        filter_params: Optional[CustomerFilter] = None,
        search_params: Optional[CustomerSearch] = None
    ) -> Tuple[List[CustomerResponse], int]:
        """Получение списка клиентов с фильтрацией и поиском"""
        try:
            # Базовый запрос для агрегации данных клиентов из заказов
            subquery = self.db.query(
                Order.customer_email,
                func.max(Order.customer_name).label('name'),
                func.max(Order.customer_phone).label('phone'),
                func.count(Order.id).label('order_count'),
                func.sum(Order.total_amount).label('total_spent'),
                func.avg(Order.total_amount).label('avg_order_value'),
                func.min(Order.created_at).label('first_order_date'),
                func.max(Order.created_at).label('last_order_date'),
                func.array_agg(Order.status.distinct()).label('order_statuses'),
                func.array_agg(Order.order_number.distinct()).label('order_numbers')
            ).filter(
                Order.shop_id == shop_id,
                Order.customer_email.isnot(None)
            ).group_by(
                Order.customer_email
            ).subquery('customer_stats')
            
            # Основной запрос
            query = self.db.query(
                subquery.c.customer_email,
                subquery.c.name,
                subquery.c.phone,
                subquery.c.order_count,
                subquery.c.total_spent,
                subquery.c.avg_order_value,
                subquery.c.first_order_date,
                subquery.c.last_order_date,
                subquery.c.order_statuses,
                subquery.c.order_numbers
            )
            
            # Применение фильтров
            if filter_params:
                if filter_params.email:
                    query = query.filter(subquery.c.customer_email.ilike(f"%{filter_params.email}%"))
                if filter_params.name:
                    query = query.filter(subquery.c.name.ilike(f"%{filter_params.name}%"))
                if filter_params.min_orders:
                    query = query.filter(subquery.c.order_count >= filter_params.min_orders)
                if filter_params.max_orders:
                    query = query.filter(subquery.c.order_count <= filter_params.max_orders)
                if filter_params.min_spent:
                    query = query.filter(subquery.c.total_spent >= filter_params.min_spent)
                if filter_params.max_spent:
                    query = query.filter(subquery.c.total_spent <= filter_params.max_spent)
                
                # Фильтр по статусу
                if filter_params.status:
                    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                    if filter_params.status == CustomerStatus.ACTIVE:
                        query = query.filter(subquery.c.last_order_date > thirty_days_ago)
                    elif filter_params.status == CustomerStatus.INACTIVE:
                        query = query.filter(subquery.c.last_order_date <= thirty_days_ago)
                
                # Фильтр по типу клиента
                if filter_params.customer_type:
                    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                    if filter_params.customer_type == CustomerType.NEW:
                        query = query.filter(subquery.c.first_order_date > thirty_days_ago)
                    elif filter_params.customer_type == CustomerType.VIP:
                        # VIP клиенты: более 10 заказов или потратили более 5000
                        query = query.filter(
                            or_(
                                subquery.c.order_count > 10,
                                subquery.c.total_spent > 5000
                            )
                        )
                    elif filter_params.customer_type == CustomerType.REGULAR:
                        query = query.filter(
                            and_(
                                subquery.c.first_order_date <= thirty_days_ago,
                                subquery.c.order_count <= 10,
                                subquery.c.total_spent <= 5000
                            )
                        )
            
            # Применение поиска
            if search_params and search_params.query:
                search_query = f"%{search_params.query}%"
                query = query.filter(
                    or_(
                        subquery.c.customer_email.ilike(search_query),
                        subquery.c.name.ilike(search_query),
                        subquery.c.phone.ilike(search_query)
                    )
                )
            
            # Получение общего количества
            total = query.count()
            
            # Применение сортировки
            sort_params = search_params or CustomerSearch()
            sort_mapping = {
                "name": subquery.c.name,
                "email": subquery.c.customer_email,
                "order_count": subquery.c.order_count,
                "total_spent": subquery.c.total_spent,
                "avg_order_value": subquery.c.avg_order_value,
                "first_order_date": subquery.c.first_order_date,
                "last_order_date": subquery.c.last_order_date
            }
            
            order_column = sort_mapping.get(sort_params.sort_by, subquery.c.last_order_date)
            if sort_params.sort_order == "desc":
                order_column = desc(order_column)
            else:
                order_column = asc(order_column)
            
            query = query.order_by(order_column)
            
            # Применение пагинации
            customers_data = query.offset(skip).limit(limit).all()
            
            # Преобразование в CustomerResponse
            customers = []
            for row in customers_data:
                # Расчет статуса и типа клиента
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                
                # Статус
                customer_status = CustomerStatus.ACTIVE if row.last_order_date > thirty_days_ago else CustomerStatus.INACTIVE
                
                # Тип
                if row.first_order_date > thirty_days_ago:
                    customer_type = CustomerType.NEW
                elif row.order_count > 10 or row.total_spent > 5000:
                    customer_type = CustomerType.VIP
                else:
                    customer_type = CustomerType.REGULAR
                
                customers.append(CustomerResponse(
                    id=0,  # Временное значение, так как ID генерируется из email
                    email=row.customer_email,
                    name=row.name,
                    phone=row.phone,
                    order_count=row.order_count,
                    total_spent=float(row.total_spent or 0),
                    avg_order_value=float(row.avg_order_value or 0),
                    first_order_date=row.first_order_date,
                    last_order_date=row.last_order_date,
                    status=customer_status,
                    type=customer_type,
                    order_statuses=row.order_statuses or [],
                    order_numbers=row.order_numbers or [],
                    created_at=row.first_order_date,
                    updated_at=row.last_order_date
                ))
            
            return customers, total
            
        except Exception as e:
            logger.error(f"Ошибка получения списка клиентов: {e}")
            raise
    
    def get_customer_stats(self, shop_id: int) -> CustomerStats:
        """Получение статистики по клиентам"""
        try:
            # Базовая статистика
            base_stats = self.db.query(
                func.count(distinct(Order.customer_email)).label('total_customers'),
                func.sum(case((Order.created_at > datetime.utcnow() - timedelta(days=30), 1), else_=0)).label('new_customers_30d'),
                func.avg(Order.total_amount).label('avg_order_value'),
                func.sum(Order.total_amount).label('total_revenue')
            ).filter(
                Order.shop_id == shop_id,
                Order.customer_email.isnot(None)
            ).first()
            
            # Активные клиенты (заказывали в течение последних 30 дней)
            active_customers = self.db.query(
                func.count(distinct(Order.customer_email))
            ).filter(
                Order.shop_id == shop_id,
                Order.created_at > datetime.utcnow() - timedelta(days=30)
            ).scalar() or 0
            
            # Статистика пожизненной ценности клиента
            lifetime_subquery = self.db.query(
                Order.customer_email,
                func.sum(Order.total_amount).label('total_spent'),
                func.count(Order.id).label('order_count')
            ).filter(
                Order.shop_id == shop_id
            ).group_by(Order.customer_email).subquery()
            
            lifetime_stats = self.db.query(
                func.avg(lifetime_subquery.c.total_spent).label('avg_lifetime_value'),
                func.max(lifetime_subquery.c.total_spent).label('max_lifetime_value'),
                func.min(lifetime_subquery.c.total_spent).label('min_lifetime_value')
            ).select_from(lifetime_subquery).first()
            
            return CustomerStats(
                total_customers=base_stats.total_customers or 0,
                active_customers=active_customers,
                inactive_customers=(base_stats.total_customers or 0) - active_customers,
                new_customers_30d=base_stats.new_customers_30d or 0,
                avg_order_value=float(base_stats.avg_order_value or 0),
                total_revenue=float(base_stats.total_revenue or 0),
                avg_lifetime_value=float(lifetime_stats.avg_lifetime_value or 0),
                max_lifetime_value=float(lifetime_stats.max_lifetime_value or 0),
                min_lifetime_value=float(lifetime_stats.min_lifetime_value or 0)
            )
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики клиентов: {e}")
            raise
    
    def get_customer_detail(self, shop_id: int, customer_email: str) -> Optional[CustomerDetail]:
        """Получение детальной информации о клиенте"""
        try:
            # Агрегированная информация о клиенте
            result = self.db.query(
                Order.customer_email,
                func.max(Order.customer_name).label('name'),
                func.max(Order.customer_phone).label('phone'),
                func.count(Order.id).label('order_count'),
                func.sum(Order.total_amount).label('total_spent'),
                func.avg(Order.total_amount).label('avg_order_value'),
                func.min(Order.created_at).label('first_order_date'),
                func.max(Order.created_at).label('last_order_date'),
                func.array_agg(Order.status.distinct()).label('order_statuses'),
                func.array_agg(Order.order_number.distinct()).label('order_numbers')
            ).filter(
                Order.shop_id == shop_id,
                Order.customer_email == customer_email
            ).group_by(
                Order.customer_email
            ).first()
            
            if not result:
                return None
            
            # Расчет статуса и типа клиента
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            # Статус
            customer_status = CustomerStatus.ACTIVE if result.last_order_date > thirty_days_ago else CustomerStatus.INACTIVE
            
            # Тип
            if result.first_order_date > thirty_days_ago:
                customer_type = CustomerType.NEW
            elif result.order_count > 10 or result.total_spent > 5000:
                customer_type = CustomerType.VIP
            else:
                customer_type = CustomerType.REGULAR
            
            # Последние заказы клиента
            recent_orders = self.db.query(Order).filter(
                Order.shop_id == shop_id,
                Order.customer_email == customer_email
            ).order_by(desc(Order.created_at)).limit(10).all()
            
            # Подготовка данных о последних заказах
            recent_orders_data = [
                {
                    "id": order.id,
                    "order_number": order.order_number,
                    "status": order.status,
                    "total_amount": float(order.total_amount),
                    "created_at": order.created_at,
                    "items": [
                        {
                            "product_name": item.product_name,
                            "quantity": item.quantity,
                            "price": float(item.price)
                        } for item in order.items
                    ] if hasattr(order, 'items') else []
                }
                for order in recent_orders
            ]
            
            return CustomerDetail(
                id=0,  # Временное значение
                email=result.customer_email,
                name=result.name,
                phone=result.phone,
                order_count=result.order_count,
                total_spent=float(result.total_spent or 0),
                avg_order_value=float(result.avg_order_value or 0),
                first_order_date=result.first_order_date,
                last_order_date=result.last_order_date,
                status=customer_status,
                type=customer_type,
                order_statuses=result.order_statuses or [],
                order_numbers=result.order_numbers or [],
                created_at=result.first_order_date,
                updated_at=result.last_order_date,
                recent_orders=recent_orders_data
            )
            
        except Exception as e:
            logger.error(f"Ошибка получения детальной информации о клиенте: {e}")
            raise
    
    def get_customer_by_email(self, shop_id: int, email: str) -> Optional[Dict[str, Any]]:
        """Получение клиента по email"""
        try:
            result = self.db.query(
                Order.customer_email,
                func.max(Order.customer_name).label('name'),
                func.max(Order.customer_phone).label('phone'),
                func.count(Order.id).label('order_count'),
                func.sum(Order.total_amount).label('total_spent')
            ).filter(
                Order.shop_id == shop_id,
                Order.customer_email == email
            ).group_by(
                Order.customer_email
            ).first()
            
            if not result:
                return None
            
            return {
                "email": result.customer_email,
                "name": result.name,
                "phone": result.phone,
                "order_count": result.order_count,
                "total_spent": float(result.total_spent or 0)
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения клиента по email: {e}")
            raise
    
    def update_customer_info(
        self, 
        shop_id: int, 
        customer_email: str, 
        name: Optional[str] = None,
        phone: Optional[str] = None
    ) -> bool:
        """Обновление информации о клиенте во всех его заказах"""
        try:
            # Обновление информации клиента во всех его заказах
            updated_count = self.db.query(Order)\
                .filter(
                    Order.shop_id == shop_id,
                    Order.customer_email == customer_email
                )\
                .update({
                    'customer_name': func.coalesce(name, Order.customer_name),
                    'customer_phone': func.coalesce(phone, Order.customer_phone),
                    'updated_at': datetime.utcnow()
                })
            
            self.db.commit()
            
            logger.info(f"Информация клиента обновлена: {customer_email}, обновлено записей: {updated_count}")
            return updated_count > 0
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка обновления информации клиента: {e}")
            return False
    
    def export_customers(self, shop_id: int, format: str = "csv") -> List[Dict[str, Any]]:
        """Экспорт данных клиентов"""
        try:
            customers = self.get_customers_from_orders(shop_id)
            
            if format == "csv":
                # Преобразование для CSV экспорта
                export_data = []
                for customer in customers:
                    export_data.append({
                        "Email": customer["email"],
                        "Имя": customer["name"] or "",
                        "Телефон": customer["phone"] or "",
                        "Количество заказов": customer["order_count"],
                        "Общая сумма": customer["total_spent"],
                        "Средний чек": customer["avg_order_value"],
                        "Первый заказ": customer["first_order_date"].strftime("%Y-%m-%d %H:%M:%S") if customer["first_order_date"] else "",
                        "Последний заказ": customer["last_order_date"].strftime("%Y-%m-%d %H:%M:%S") if customer["last_order_date"] else "",
                        "Статус": customer["status"],
                        "Тип": customer["type"]
                    })
                return export_data
            else:
                return customers
                
        except Exception as e:
            logger.error(f"Ошибка экспорта клиентов: {e}")
            raise