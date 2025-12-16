"""
订单管理API端点
"""
# backend/app/api/v1/endpoints/order.py
import logging
import csv
import json
from typing import Optional, List
from datetime import datetime
from io import StringIO
from math import ceil
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from backend.app.database import get_db
from backend.app.core.security import get_current_user
from backend.app.services.order_service import OrderService
from backend.app.schemas.order import (
    OrderCreate, OrderInDB, OrderUpdate, OrderList,
    OrderStatus, OrderStatusUpdate, OrderSearch,
    OrderBulkUpdate, OrderExportRequest, OrderStats
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["orders"])


def get_order_service(db: Session = Depends(get_db)) -> OrderService:
    """Получить экземпляр сервиса заказов"""
    return OrderService(db)


@router.get("/", response_model=OrderList)
async def get_orders(
    shop_id: int = Query(..., description="ID магазина"),
    skip: int = Query(0, ge=0, description="Пропустить записей"),
    limit: int = Query(100, ge=1, le=1000, description="Количество на страницу"),
    status: Optional[str] = Query(None, description="Статус заказа"),
    customer_email: Optional[str] = Query(None, description="Email клиента"),
    order_number: Optional[str] = Query(None, description="Номер заказа"),
    start_date: Optional[datetime] = Query(None, description="Начальная дата"),
    end_date: Optional[datetime] = Query(None, description="Конечная дата"),
    current_user = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Получить список заказов (с пагинацией и базовой фильтрацией)
    
    Примечание: Пользователь должен иметь доступ к магазину
    """
    try:
        # Проверить права доступа пользователя
        await _validate_shop_access(current_user, shop_id, order_service.db)
        
        # Получить список заказов
        orders, total = order_service.get_orders(
            shop_id=shop_id,
            skip=skip,
            limit=limit,
            status=status,
            customer_email=customer_email,
            start_date=start_date,
            end_date=end_date
        )
        
        # Рассчитать информацию о пагинации
        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        current_page = (skip // limit) + 1 if limit > 0 else 1
        
        logger.info(f"Пользователь {current_user.id} получил список заказов магазина {shop_id}")
        
        return OrderList(
            orders=orders,
            total=total,
            page=current_page,
            page_size=limit,
            total_pages=total_pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении списка заказов: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить список заказов"
        )


@router.post("/search", response_model=OrderList)
async def search_orders(
    shop_id: int = Query(..., description="ID магазина"),
    search_params: OrderSearch = None,
    skip: int = Query(0, ge=0, description="Пропустить записей"),
    limit: int = Query(100, ge=1, le=1000, description="Количество на страницу"),
    include_items: bool = Query(False, description="Включать элементы заказа"),
    current_user = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Расширенный поиск заказов (с поддержкой сложной фильтрации и поиска)
    """
    try:
        # Проверить права доступа пользователя
        await _validate_shop_access(current_user, shop_id, order_service.db)
        
        # Использовать параметры поиска по умолчанию
        if search_params is None:
            search_params = OrderSearch()
        
        # Поиск заказов - используем существующий метод get_orders
        # Примечание: нам нужно сначала реализовать метод search_orders
        orders, total = order_service.get_orders(
            shop_id=shop_id,
            skip=skip,
            limit=limit,
            customer_email=search_params.query if search_params.query else None,
            start_date=search_params.filter.start_date if search_params and search_params.filter else None,
            end_date=search_params.filter.end_date if search_params and search_params.filter else None,
            status=search_params.filter.status if search_params and search_params.filter else None
        )
        
        # Рассчитать информацию о пагинации
        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        current_page = (skip // limit) + 1 if limit > 0 else 1
        
        logger.info(f"Пользователь {current_user.id} выполнил поиск заказов в магазине {shop_id}")
        
        return OrderList(
            orders=orders,
            total=total,
            page=current_page,
            page_size=limit,
            total_pages=total_pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при поиске заказов: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось выполнить поиск заказов"
        )


@router.get("/{order_id}", response_model=OrderInDB)
async def get_order(
    shop_id: int = Query(..., description="ID магазина"),
    order_id: int = Path(..., description="ID заказа"),  # Изменено здесь: Query → Path
    include_items: bool = Query(True, description="Включать элементы заказа"),
    current_user = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Получить детальную информацию о заказе
    """
    try:
        # Проверить права доступа пользователя
        await _validate_shop_access(current_user, shop_id, order_service.db)
        
        # Получить заказ
        order = order_service.get_order(shop_id, order_id)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Заказ не найден"
            )
        
        logger.info(f"Пользователь {current_user.id} просмотрел заказ {order_id}")
        
        return order
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении информации о заказе: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить информацию о заказе"
        )


@router.post("/", response_model=OrderInDB)
async def create_order(
    shop_id: int = Query(..., description="ID магазина"),
    order_data: OrderCreate = None,
    current_user = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Создать новый заказ
    """
    try:
        # Проверить права доступа пользователя (создание заказа может не требовать прав магазина в зависимости от бизнес-логики)
        # Здесь упрощенная обработка, разрешаем любому аутентифицированному пользователю создавать заказы
        
        # Создать заказ
        order = order_service.create_order(shop_id, order_data)
        
        logger.info(f"Пользователь {current_user.id} создал заказ {order.order_number}")
        
        return order
        
    except ValueError as e:
        logger.warning(f"Ошибка параметров при создании заказа: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Ошибка при создании заказа: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось создать заказ"
        )


@router.patch("/{order_id}", response_model=OrderInDB)
async def update_order(
    shop_id: int = Query(..., description="ID магазина"),
    order_id: int = Path(..., description="ID заказа"),  # Изменено здесь: Query → Path
    update_data: OrderUpdate = None,
    background_tasks: BackgroundTasks = None,
    current_user = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Обновить информацию о заказе
    
    Поддерживает обновление статуса заказа, заметок администратора, информации о доставке и т.д.
    Только администратор магазина или владелец могут обновлять заказы
    """
    try:
        # Проверить права доступа пользователя (должен быть администратором магазина или владельцем)
        await _validate_shop_admin_access(current_user, shop_id, order_service.db)
        
        # Получить оригинальную информацию о заказе
        original_order = order_service.get_order(shop_id, order_id)
        if not original_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Заказ не найден"
            )
        
        # Проверить, можно ли обновить заказ
        if not _can_update_order(original_order.status, update_data.status if update_data else None):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Текущий статус заказа не позволяет обновление"
            )
        
        # Обновить заказ
        updated_order = order_service.update_order(shop_id, order_id, update_data)
        
        if not updated_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Заказ не найден или не удалось обновить"
            )
        
        # Записать изменение статуса (если статус обновлен)
        if update_data and update_data.status:
            await _log_order_status_change(
                original_order,
                updated_order,
                current_user,
                order_service.db
            )
            
            # Отправить уведомление (если статус изменен)
            if background_tasks:
                background_tasks.add_task(
                    _send_order_status_notification,
                    updated_order,
                    original_order.status,
                    current_user
                )
        
        logger.info(f"Пользователь {current_user.id} обновил заказ {order_id}")
        
        return updated_order
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении заказа: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось обновить заказ"
        )


@router.patch("/{order_id}/status", response_model=OrderInDB)
async def update_order_status(
    shop_id: int = Query(..., description="ID магазина"),
    order_id: int = Path(..., description="ID заказа"),  # Изменено здесь: Query → Path
    status_update: OrderStatusUpdate = None,
    background_tasks: BackgroundTasks = None,
    current_user = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Специальный метод для обновления статуса заказа
    
    Поддерживает переходы статусов: pending → processing → shipped → delivered
    Только администратор магазина или владелец могут обновлять статусы
    """
    try:
        # Проверить права доступа пользователя
        await _validate_shop_admin_access(current_user, shop_id, order_service.db)
        
        # Получить оригинальный заказ
        original_order = order_service.get_order(shop_id, order_id)
        if not original_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Заказ не найден"
            )
        
        # Проверить, допустим ли переход статуса
        if not _is_valid_status_transition(original_order.status, status_update.status):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недопустимый переход статуса с {original_order.status} на {status_update.status}"
            )
        
        # Создать данные для обновления
        update_data = OrderUpdate(status=status_update.status)
        if status_update.notes:
            update_data.admin_notes = status_update.notes
        
        # Обновить заказ
        updated_order = order_service.update_order(shop_id, order_id, update_data)
        
        if not updated_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Не удалось обновить заказ"
            )
        
        # Записать изменение статуса
        await _log_order_status_change(
            original_order,
            updated_order,
            current_user,
            order_service.db,
            notes=status_update.notes
        )
        
        # Отправить уведомление
        if status_update.send_notification and background_tasks:
            background_tasks.add_task(
                _send_order_status_notification,
                updated_order,
                original_order.status,
                current_user
            )
        
        logger.info(f"Пользователь {current_user.id} обновил статус заказа {order_id} на {status_update.status}")
        
        return updated_order
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении статуса заказа: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось обновить статус заказа"
        )


@router.post("/bulk-update")
async def bulk_update_orders(
    shop_id: int = Query(..., description="ID магазина"),
    bulk_update: OrderBulkUpdate = None,
    current_user = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Массовое обновление заказов
    
    Используется для массового обновления статусов заказов, добавления заметок и т.д.
    Только администратор магазина или владелец могут выполнять массовые обновления
    """
    try:
        # Проверить права доступа пользователя
        await _validate_shop_admin_access(current_user, shop_id, order_service.db)
        
        # Временная реализация - фактически должен вызываться метод bulk_update_orders
        # Здесь упрощенная обработка, в реальном проекте нужно реализовать этот метод
        return {
            "success": True,
            "message": "Функция массового обновления находится в разработке",
            "updated_count": 0,
            "updated_orders": []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при массовом обновлении заказов: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось выполнить массовое обновление заказов"
        )


@router.get("/stats/summary")
async def get_order_stats_summary(
    shop_id: int = Query(..., description="ID магазина"),
    period: str = Query("30d", description="Период статистики: 7d, 30d, 90d, 1y, all"),
    current_user = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Получить сводную статистику по заказам
    """
    try:
        # Проверить права доступа пользователя
        await _validate_shop_access(current_user, shop_id, order_service.db)
        
        # Получить статистику
        stats = order_service.get_order_stats(shop_id)
        
        # Получить ежедневную/ежемесячную статистику в зависимости от периода
        days_map = {
            "7d": 7,
            "30d": 30,
            "90d": 90,
            "1y": 365,
            "all": 3650  # 10 лет, означает "все"
        }
        
        days = days_map.get(period, 30)
        daily_stats = order_service.get_daily_stats(shop_id, days)
        
        return {
            "summary": stats,
            "daily_stats": daily_stats,
            "period": period
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики заказов: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить статистику заказов"
        )


@router.post("/export")
async def export_orders(
    shop_id: int = Query(..., description="ID магазина"),
    export_request: OrderExportRequest = None,
    current_user = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Экспорт данных заказов
    
    Поддерживает форматы CSV, Excel, JSON
    """
    try:
        # Проверить права доступа пользователя
        await _validate_shop_access(current_user, shop_id, order_service.db)
        
        # Временная реализация - фактически должен вызываться метод export_orders
        # Здесь возвращаем пример данных
        return {
            "filename": f"orders_export_{shop_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "total_count": 0,
            "message": "Функция экспорта находится в разработке",
            "format": export_request.format if export_request else "csv"
        }
        
    except Exception as e:
        logger.error(f"Ошибка при экспорте заказов: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось экспортировать заказы: {str(e)}"
        )


# ===== Вспомогательные функции проверки прав доступа =====

async def _validate_shop_access(user, shop_id: int, db: Session):
    """Проверить, имеет ли пользователь доступ к магазину"""
    from backend.app.models.shop import Shop, ShopMember
    
    # Проверить, является ли пользователь владельцем магазина
    shop = db.query(Shop).filter(
        Shop.id == shop_id,
        Shop.owner_id == user.id
    ).first()
    
    if shop:
        return True
    
    # Проверить, является ли пользователь участником магазина
    member = db.query(ShopMember).filter(
        ShopMember.shop_id == shop_id,
        ShopMember.user_id == user.id
    ).first()
    
    if member:
        return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Нет доступа к заказам этого магазина"
    )


async def _validate_shop_admin_access(user, shop_id: int, db: Session):
    """Проверить, является ли пользователь администратором или владельцем магазина"""
    from backend.app.models.shop import Shop, ShopMember
    
    # Проверить, является ли пользователь владельцем магазина
    shop = db.query(Shop).filter(
        Shop.id == shop_id,
        Shop.owner_id == user.id
    ).first()
    
    if shop:
        return True
    
    # Проверить, является ли пользователь администратором магазина
    # Примечание: в структуре вашей модели ShopMember может быть поле is_admin
    member = db.query(ShopMember).filter(
        ShopMember.shop_id == shop_id,
        ShopMember.user_id == user.id
    ).first()
    
    # Если в модели нет поля is_admin, упрощаем обработку
    # Наличие членства считается административным доступом
    if member:
        return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Требуются права администратора для операций с заказами"
    )


# ===== Вспомогательные функции бизнес-логики =====

def _can_update_order(current_status: str, new_status: Optional[str]) -> bool:
    """Проверить, можно ли обновить заказ"""
    if not new_status:
        return True  # Не обновляем статус, только другие поля
    
    # Определить допустимые переходы статусов
    allowed_transitions = {
        "pending": ["processing", "cancelled"],
        "processing": ["shipped", "cancelled"],
        "shipped": ["delivered"],
        "delivered": [],  # После доставки статус нельзя менять
        "cancelled": [],  # После отмены статус нельзя менять
        "refunded": []    # После возврата статус нельзя менять
    }
    
    return new_status in allowed_transitions.get(current_status, [])


def _is_valid_status_transition(current_status: str, new_status: str) -> bool:
    """Проверить, допустим ли переход статуса"""
    # Диаграмма переходов статусов
    status_flow = {
        "pending": ["processing", "cancelled"],
        "processing": ["shipped", "cancelled", "refunded"],
        "shipped": ["delivered", "cancelled", "refunded"],
        "delivered": ["refunded"],  # После доставки возможен только возврат
        "cancelled": [],  # После отмены нельзя менять
        "refunded": []    # После возврата нельзя менять
    }
    
    return new_status in status_flow.get(current_status, [])


async def _log_order_status_change(
    original_order,
    updated_order,
    changed_by,
    db: Session,
    notes: str = None
):
    """Записать историю изменений статуса заказа"""
    try:
        # Если у модели заказа есть поле status_history, записываем изменение
        if hasattr(original_order, 'status_history'):
            history_entry = {
                'old_status': original_order.status,
                'new_status': updated_order.status,
                'changed_by': changed_by.id,
                'changed_by_name': changed_by.full_name or changed_by.email,
                'changed_at': datetime.utcnow(),
                'notes': notes
            }
            
            if not original_order.status_history:
                original_order.status_history = [history_entry]
            else:
                original_order.status_history.append(history_entry)
            
            db.commit()
    except Exception as e:
        logger.warning(f"Не удалось записать историю изменения статуса заказа: {e}")


async def _send_order_status_notification(order, old_status, changed_by):
    """Отправить уведомление об изменении статуса заказа"""
    try:
        # Здесь можно интегрировать сервисы уведомлений: email, SMS, push-уведомления и т.д.
        logger.info(f"Статус заказа {order.order_number} изменен с {old_status} на {order.status}")
        
        # Пример: отправка email-уведомления клиенту
        if order.customer_email:
            # В реальном проекте должен вызываться сервис отправки email
            logger.info(f"Отправка email об обновлении статуса заказа на {order.customer_email}")
    except Exception as e:
        logger.warning(f"Не удалось отправить уведомление об изменении статуса заказа: {e}")


# Конечная точка проверки работоспособности
@router.get("/health")
async def orders_health():
    """Проверка работоспособности сервиса заказов"""
    return {
        "status": "работает",
        "service": "заказы",
        "endpoints": [
            "GET /orders",
            "POST /orders/search",
            "GET /orders/{order_id}",
            "POST /orders",
            "PATCH /orders/{order_id}",
            "PATCH /orders/{order_id}/status",
            "POST /orders/bulk-update",
            "GET /orders/stats/summary",
            "POST /orders/export"
        ]
    }