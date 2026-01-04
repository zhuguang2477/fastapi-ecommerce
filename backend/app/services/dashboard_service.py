# backend/app/services/dashboad_service.py
"""
仪表板统计服务
聚合店铺统计数据并处理缓存
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any 
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, extract, and_, case
from sqlalchemy.sql import label
from backend.app.models.category import Category
from backend.app.models.product import Product
from backend.app.models.order import Order
from backend.app.models.customer import Customer
from backend.app.models.shop import Shop 

from backend.app.core.cache import dashboard_cache
from backend.app.schemas.dashboard import (
    DashboardStats, CategoryStat, MonthlyRevenue, UserActivity
)

logger = logging.getLogger(__name__)


class DashboardService:
    """Сервис статистики панели управления"""
    
    def __init__(self, db: Session):
        self.db = db
    
    @dashboard_cache(ttl=300)
    async def get_dashboard_stats(self, shop_id: int) -> DashboardStats:
        """
        Получить статистику для панели управления
        
        Args:
            shop_id: ID магазина
            
        Returns:
            DashboardStats: Статистика панели управления
        """
        logger.info(f"Получение статистики панели управления для магазина {shop_id}...")
        
        try:
            # Параллельное получение всей статистики
            popular_categories = await self._get_popular_categories(shop_id)
            user_activity = await self._get_user_activity(shop_id)
            avg_product_rating = await self._get_average_product_rating(shop_id)
            avg_order_value = await self._get_average_order_value(shop_id)
            monthly_revenue = await self._get_monthly_revenue(shop_id)
            
            return DashboardStats(
                popular_categories=popular_categories,
                user_activity=user_activity,
                average_product_rating=avg_product_rating,
                average_order_value=avg_order_value,
                monthly_revenue=monthly_revenue
            )
        except Exception as e:
            logger.error(f"Ошибка получения статистики панели управления: {e}")
            # Возвращаем пустые данные, чтобы избежать ошибок API
            return DashboardStats(
                popular_categories=[],
                user_activity=UserActivity(week=[], visits=[]),
                average_product_rating=0.0,
                average_order_value=0.0,
                monthly_revenue=[]
            )
    
    
    async def _get_popular_categories(self, shop_id: int) -> List[CategoryStat]:
        """
        Получить популярные категории (по количеству товаров)
        
        Можно сортировать по следующим критериям:
        1. Наибольшее количество товаров
        2. Наибольшее количество заказов
        3. Наибольший объем продаж
        """
        try:
            # Статистика по категориям по количеству товаров
            category_stats = self.db.query(
                Category.name,
                func.count(Product.id).label('product_count')
            ).join(
                Product, Category.id == Product.category_id, isouter=True
            ).filter(
                Category.shop_id == shop_id,
                Category.is_active == True
            ).group_by(
                Category.id, Category.name
            ).order_by(
                desc('product_count')
            ).limit(10).all()
            
            return [
                CategoryStat(name=name, count=count)
                for name, count in category_stats
            ]
        except Exception as e:
            logger.error(f"Ошибка получения популярных категорий: {e}")
            return []
    
    async def _get_user_activity(self, shop_id: int) -> UserActivity:
        """
        Получить график активности пользователей по неделям (последние 8 недель)
        
        Статистика по неделям:
        1. Количество новых заказов
        2. Количество новых клиентов
        3. Количество активных клиентов
        """
        try:
            # Получить номера недель за последние 8 недель
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(weeks=8)
            
            # Статистика заказов по неделям
            weekly_orders = self.db.query(
                func.date_trunc('week', Order.created_at).label('week'),
                func.count(Order.id).label('order_count')
            ).filter(
                Order.shop_id == shop_id,
                Order.created_at >= start_date,
                Order.created_at <= end_date
            ).group_by(
                func.date_trunc('week', Order.created_at)
            ).order_by('week').all()
            
            # Статистика новых клиентов по неделям
            weekly_customers = self.db.query(
                func.date_trunc('week', Customer.registered_at).label('week'),
                func.count(Customer.id).label('customer_count')
            ).filter(
                Customer.shop_id == shop_id,
                Customer.registered_at >= start_date,
                Customer.registered_at <= end_date
            ).group_by(
                func.date_trunc('week', Customer.registered_at)
            ).order_by('week').all()
            
            # Преобразование данных в формат словаря
            order_dict = {str(row.week.date()): row.order_count for row in weekly_orders}
            customer_dict = {str(row.week.date()): row.customer_count for row in weekly_customers}
            
            # Генерация полного списка недель
            weeks = []
            order_counts = []
            customer_counts = []
            
            current_date = start_date
            while current_date <= end_date:
                week_start = current_date - timedelta(days=current_date.weekday())
                week_str = week_start.strftime("%Y-%m-%d")
                
                if week_str not in weeks:
                    weeks.append(week_str)
                    order_counts.append(order_dict.get(week_str, 0))
                    customer_counts.append(customer_dict.get(week_str, 0))
                
                current_date += timedelta(days=7)
            
            # Здесь мы возвращаем только количество заказов как показатель активности пользователей
            # Можно адаптировать под требования: возвращать сумму заказов+клиентов или отображать отдельно
            return UserActivity(
                week=weeks,
                visits=order_counts
            )
            
        except Exception as e:
            logger.error(f"Ошибка получения данных активности пользователей: {e}")
            return UserActivity(week=[], visits=[])
    
    async def _get_average_product_rating(self, shop_id: int) -> float:
        """
        Получить средний рейтинг товаров
        
        Рассчитать средневзвешенный рейтинг всех опубликованных товаров
        """
        try:
            # Статистика среднего рейтинга всех опубликованных товаров
            # Примечание: у модели Product может не быть поля average_rating, нужно проверить
            avg_rating = self.db.query(
                func.avg(Product.average_rating).label('avg_rating')
            ).filter(
                Product.shop_id == shop_id,
                Product.status == 'active',
                Product.average_rating > 0
            ).scalar()
            
            return float(avg_rating or 0)
        except Exception as e:
            logger.error(f"Ошибка получения среднего рейтинга товаров: {e}")
            return 0.0
    
    async def _get_average_order_value(self, shop_id: int) -> float:
        """
        Получить среднюю стоимость заказа
        
        Формула расчета: общий объем продаж / количество заказов
        """
        try:
            # Получить статистику заказов за последние 30 дней
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            stats = self.db.query(
                func.count(Order.id).label('order_count'),
                func.sum(Order.total_amount).label('total_revenue')
            ).filter(
                Order.shop_id == shop_id,
                Order.created_at >= thirty_days_ago,
                Order.status.in_(['paid', 'delivered'])
            ).first()
            
            if stats and stats.order_count and stats.order_count > 0:
                return float(stats.total_revenue or 0) / stats.order_count
            return 0.0
        except Exception as e:
            logger.error(f"Ошибка получения средней стоимости заказа: {e}")
            return 0.0
    
    async def _get_monthly_revenue(self, shop_id: int) -> List[MonthlyRevenue]:
        """
        Получить график месячной выручки (последние 12 месяцев)
        """
        try:
            # Получить данные за последние 12 месяцев
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=365)
            
            monthly_stats = self.db.query(
                func.date_trunc('month', Order.created_at).label('month'),
                func.sum(Order.total_amount).label('revenue'),
                func.count(Order.id).label('order_count')
            ).filter(
                Order.shop_id == shop_id,
                Order.created_at >= start_date,
                Order.created_at <= end_date,
                Order.status.in_(['paid', 'delivered'])
            ).group_by(
                func.date_trunc('month', Order.created_at)
            ).order_by('month').all()
            
            return [
                MonthlyRevenue(
                    month=row.month.strftime("%Y-%m"),
                    revenue=float(row.revenue or 0)
                )
                for row in monthly_stats
            ]
        except Exception as e:
            logger.error(f"Ошибка получения данных месячной выручки: {e}")
            return []
    
    async def get_quick_stats(self, shop_id: int) -> Dict[str, Any]:
        """
        Получить быструю статистику (для карточек панели управления)
        """
        try:
            # Заказы за сегодня
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_orders = self.db.query(func.count(Order.id)).filter(
                Order.shop_id == shop_id,
                Order.created_at >= today_start,
                Order.status != 'cancelled'
            ).scalar() or 0
            
            # Выручка за сегодня
            today_revenue = self.db.query(func.sum(Order.total_amount)).filter(
                Order.shop_id == shop_id,
                Order.created_at >= today_start,
                Order.status.in_(['paid', 'delivered'])
            ).scalar() or 0
            
            # Общее количество товаров
            total_products = self.db.query(func.count(Product.id)).filter(
                Product.shop_id == shop_id,
                Product.status == 'active'
            ).scalar() or 0
            
            # Общее количество клиентов
            total_customers = self.db.query(func.count(Customer.id)).filter(
                Customer.shop_id == shop_id,
                Customer.is_active == True
            ).scalar() or 0
            
            # Товары отсутствуют на складе
            out_of_stock = self.db.query(func.count(Product.id)).filter(
                Product.shop_id == shop_id,
                Product.stock_quantity <= 0,
                Product.status == 'active'
            ).scalar() or 0
            
            # Ожидающие заказы
            pending_orders = self.db.query(func.count(Order.id)).filter(
                Order.shop_id == shop_id,
                Order.status == 'pending'
            ).scalar() or 0
            
            return {
                'today_orders': today_orders,
                'today_revenue': float(today_revenue),
                'total_products': total_products,
                'total_customers': total_customers,
                'out_of_stock': out_of_stock,
                'pending_orders': pending_orders
            }
        except Exception as e:
            logger.error(f"Ошибка получения быстрой статистики: {e}")
            return {}
    
    async def refresh_dashboard_cache(self, shop_id: int):
        """
        Обновить кэш панели управления
        
        Вызвать этот метод после обновления данных для обновления кэша
        """
        try:
            from backend.app.core.cache import cache_service
            
            # Очистить весь кэш панели управления, связанный с магазином
            pattern = f"cache:dashboard:*shop_{shop_id}*"
            await cache_service.clear_pattern(pattern)
            logger.info(f"Кэш панели управления для магазина {shop_id} обновлен")
        except Exception as e:
            logger.error(f"Ошибка обновления кэша панели управления: {e}")


# Вспомогательная функция для получения сервиса панели управления
def get_dashboard_service(db: Session) -> DashboardService:
    """Получить экземпляр сервиса панели управления"""
    return DashboardService(db)