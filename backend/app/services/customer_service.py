# backend/app/services/customer_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_, distinct, case
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging

from backend.app.models.order import Order
from backend.app.models.customer import Customer
from backend.app.schemas.customer import CustomerResponse, CustomerList

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
                
                # Если новый клиент (первый заказ в течение последних 30 дней)
                if result.first_order_date > thirty_days_ago:
                    customer_type = "new"
                else:
                    customer_type = "regular"
                
                customers.append({
                    "email": result.customer_email,
                    "name": result.name,
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
        email: Optional[str] = None,
        name: Optional[str] = None,
        status: Optional[str] = None,
        customer_type: Optional[str] = None,
        min_orders: Optional[int] = None,
        max_orders: Optional[int] = None,
        min_spent: Optional[float] = None,
        max_spent: Optional[float] = None,
        sort_by: str = "last_order_date",
        sort_order: str = "desc"
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Получение списка клиентов (агрегация из заказов)"""
        try:
            # Базовый запрос
            query = self.db.query(
                Order.customer_email,
                func.max(Order.customer_name).label('name'),
                func.count(Order.id).label('order_count'),
                func.sum(Order.total_amount).label('total_spent'),
                func.avg(Order.total_amount).label('avg_order_value'),
                func.min(Order.created_at).label('first_order_date'),
                func.max(Order.created_at).label('last_order_date'),
                func.array_agg(Order.status.distinct()).label('order_statuses'),
                func.array_agg(Order.order_number).label('order_numbers')
            ).filter(
                Order.shop_id == shop_id,
                Order.customer_email.isnot(None)
            )
            
            # Применение фильтров
            if email:
                query = query.filter(Order.customer_email.ilike(f"%{email}%"))
            
            if name:
                query = query.filter(Order.customer_name.ilike(f"%{name}%"))
            
            # Применение группировки
            query = query.group_by(Order.customer_email)
            
            # Применение пост-фильтрации (требуется подзапрос, так как условия зависят от агрегатных результатов)
            from sqlalchemy.orm import aliased
            
            # Создание подзапроса
            subquery = query.subquery()
            
            main_query = self.db.query(
                subquery.c.customer_email,
                subquery.c.name,
                subquery.c.order_count,
                subquery.c.total_spent,
                subquery.c.avg_order_value,
                subquery.c.first_order_date,
                subquery.c.last_order_date,
                subquery.c.order_statuses,
                subquery.c.order_numbers
            )
            
            # Применение условий фильтрации после агрегации
            if min_orders:
                main_query = main_query.filter(subquery.c.order_count >= min_orders)
            
            if max_orders:
                main_query = main_query.filter(subquery.c.order_count <= max_orders)
            
            if min_spent:
                main_query = main_query.filter(subquery.c.total_spent >= min_spent)
            
            if max_spent:
                main_query = main_query.filter(subquery.c.total_spent <= max_spent)
            
            # Применение фильтра по статусу
            if status == "active":
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                main_query = main_query.filter(subquery.c.last_order_date > thirty_days_ago)
            elif status == "inactive":
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                main_query = main_query.filter(subquery.c.last_order_date <= thirty_days_ago)
            
            # Применение фильтра по типу клиента
            if customer_type == "new":
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                main_query = main_query.filter(subquery.c.first_order_date > thirty_days_ago)
            elif customer_type == "regular":
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                main_query = main_query.filter(subquery.c.first_order_date <= thirty_days_ago)
            
            # Получение общего количества
            total = main_query.count()
            
            # Применение сортировки
            sort_mapping = {
                "name": subquery.c.name,
                "email": subquery.c.customer_email,
                "order_count": subquery.c.order_count,
                "total_spent": subquery.c.total_spent,
                "avg_order_value": subquery.c.avg_order_value,
                "first_order_date": subquery.c.first_order_date,
                "last_order_date": subquery.c.last_order_date
            }
            
            order_column = sort_mapping.get(sort_by, subquery.c.last_order_date)
            if sort_order == "desc":
                order_column = desc(order_column)
            
            main_query = main_query.order_by(order_column)
            
            # Применение пагинации
            customers_data = main_query.offset(skip).limit(limit).all()
            
            # Обработка результатов
            customers = []
            for row in customers_data:
                # Расчет статуса и типа клиента
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                customer_status = "active" if row.last_order_date > thirty_days_ago else "inactive"
                customer_type = "new" if row.first_order_date > thirty_days_ago else "regular"
                
                customers.append({
                    "email": row.customer_email,
                    "name": row.name,
                    "order_count": row.order_count,
                    "total_spent": float(row.total_spent or 0),
                    "avg_order_value": float(row.avg_order_value or 0),
                    "first_order_date": row.first_order_date,
                    "last_order_date": row.last_order_date,
                    "status": customer_status,
                    "type": customer_type,
                    "order_statuses": row.order_statuses or [],
                    "order_numbers": row.order_numbers or []
                })
            
            return customers, total
            
        except Exception as e:
            logger.error(f"Ошибка получения списка клиентов: {e}")
            raise
    
    def get_customer_stats(self, shop_id: int) -> Dict[str, Any]:
        """Получение статистики по клиентам"""
        try:
            # Получение базовой статистики из заказов
            result = self.db.query(
                func.count(distinct(Order.customer_email)).label('total_customers'),
                func.sum(case((Order.created_at > datetime.utcnow() - timedelta(days=30), 1), else_=0)).label('new_customers_30d'),
                func.avg(Order.total_amount).label('avg_order_value'),
                func.sum(Order.total_amount).label('total_revenue')
            ).filter(
                Order.shop_id == shop_id,
                Order.customer_email.isnot(None)
            ).first()
            
            # Количество активных клиентов (заказывали в течение последних 30 дней)
            active_customers = self.db.query(
                func.count(distinct(Order.customer_email))
            ).filter(
                Order.shop_id == shop_id,
                Order.created_at > datetime.utcnow() - timedelta(days=30)
            ).scalar() or 0
            
            # Статистика пожизненной ценности клиента
            lifetime_subquery = self.db.query(
                Order.customer_email,
                func.sum(Order.total_amount).label('total_spent')
            ).filter(
                Order.shop_id == shop_id
            ).group_by(Order.customer_email).subquery()
            
            customer_lifetime_stats = self.db.query(
                func.avg(lifetime_subquery.c.total_spent).label('avg_lifetime_value'),
                func.max(lifetime_subquery.c.total_spent).label('max_lifetime_value'),
                func.min(lifetime_subquery.c.total_spent).label('min_lifetime_value')
            ).select_from(
                lifetime_subquery
            ).first()
            
            return {
                "total_customers": result.total_customers or 0,
                "active_customers": active_customers,
                "inactive_customers": (result.total_customers or 0) - active_customers,
                "new_customers_30d": result.new_customers_30d or 0,
                "avg_order_value": float(result.avg_order_value or 0),
                "total_revenue": float(result.total_revenue or 0),
                "avg_lifetime_value": float(customer_lifetime_stats.avg_lifetime_value or 0),
                "max_lifetime_value": float(customer_lifetime_stats.max_lifetime_value or 0),
                "min_lifetime_value": float(customer_lifetime_stats.min_lifetime_value or 0),
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики клиентов: {e}")
            raise
    
    def get_customer_detail(self, shop_id: int, customer_email: str) -> Optional[Dict[str, Any]]:
        """Получение детальной информации о клиенте"""
        try:
            # Получение агрегированной информации о клиенте
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
                func.array_agg(Order.order_number).label('order_numbers')
            ).filter(
                Order.shop_id == shop_id,
                Order.customer_email == customer_email
            ).group_by(
                Order.customer_email
            ).first()
            
            if not result:
                return None
            
            # Расчет статуса клиента
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            customer_status = "active" if result.last_order_date > thirty_days_ago else "inactive"
            customer_type = "new" if result.first_order_date > thirty_days_ago else "regular"
            
            # Получение последних заказов клиента
            recent_orders = self.db.query(Order).filter(
                Order.shop_id == shop_id,
                Order.customer_email == customer_email
            ).order_by(
                desc(Order.created_at)
            ).limit(10).all()
            
            return {
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
                "order_statuses": result.order_statuses or [],
                "order_numbers": result.order_numbers or [],
                "recent_orders": [
                    {
                        "order_number": order.order_number,
                        "status": order.status.value,
                        "total_amount": float(order.total_amount),
                        "created_at": order.created_at
                    }
                    for order in recent_orders
                ]
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения детальной информации о клиенте: {e}")
            raise