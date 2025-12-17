# backend/app/api/v1/endpoints/customers.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import json

from backend.app.database import get_db
from backend.app.core.security import get_current_user
from backend.app.schemas.customer import (
    CustomerResponse, CustomerList, CustomerDetail,
    CustomerStats, CustomerFilter, CustomerSearch,
    CustomerStatus, CustomerType
)
from backend.app.services.customer_service import CustomerService

router = APIRouter()
logger = logging.getLogger(__name__)

# Эндпоинты управления клиентами
@router.get("/shops/{shop_id}/customers", response_model=CustomerList)
async def get_customers(
    shop_id: int = Path(..., description="ID магазина"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    email: Optional[str] = Query(None, description="Поиск по email"),
    name: Optional[str] = Query(None, description="Поиск по имени"),
    status: Optional[CustomerStatus] = Query(None, description="Статус клиента"),
    customer_type: Optional[CustomerType] = Query(None, description="Тип клиента"),
    min_orders: Optional[int] = Query(None, ge=0, description="Минимальное количество заказов"),
    max_orders: Optional[int] = Query(None, ge=0, description="Максимальное количество заказов"),
    min_spent: Optional[float] = Query(None, ge=0, description="Минимальная сумма покупок"),
    max_spent: Optional[float] = Query(None, ge=0, description="Максимальная сумма покупок"),
    sort_by: str = Query("last_order_date", description="Поле для сортировки"),
    sort_order: str = Query("desc", description="Порядок сортировки"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить список клиентов (агрегировано из данных заказов)"""
    try:
        customer_service = CustomerService(db)
        
        customers, total = customer_service.get_customers(
            shop_id=shop_id,
            skip=skip,
            limit=limit,
            email=email,
            name=name,
            status=status.value if status else None,
            customer_type=customer_type.value if customer_type else None,
            min_orders=min_orders,
            max_orders=max_orders,
            min_spent=min_spent,
            max_spent=max_spent,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Рассчитать информацию о пагинации
        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        current_page = (skip // limit) + 1 if limit > 0 else 1
        
        return CustomerList(
            customers=customers,
            total=total,
            page=current_page,
            page_size=limit,
            total_pages=total_pages
        )
    except Exception as e:
        logger.error(f"Ошибка при получении списка клиентов: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить список клиентов")

@router.get("/shops/{shop_id}/customers/{customer_email}", response_model=CustomerDetail)
async def get_customer_detail(
    shop_id: int = Path(..., description="ID магазина"),
    customer_email: str = Path(..., description="Email клиента"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить детальную информацию о клиенте"""
    try:
        customer_service = CustomerService(db)
        customer = customer_service.get_customer_detail(shop_id, customer_email)
        
        if not customer:
            raise HTTPException(status_code=404, detail="Клиент не найден")
        
        return customer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении детальной информации о клиенте: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить информацию о клиенте")

@router.get("/shops/{shop_id}/customers/stats", response_model=CustomerStats)
async def get_customer_stats(
    shop_id: int = Path(..., description="ID магазина"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить статистику по клиентам"""
    try:
        customer_service = CustomerService(db)
        stats = customer_service.get_customer_stats(shop_id)
        return stats
    except Exception as e:
        logger.error(f"Ошибка при получении статистики клиентов: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить статистику клиентов")

@router.get("/shops/{shop_id}/customers/export")
async def export_customers(
    shop_id: int = Path(..., description="ID магазина"),
    format: str = Query("json", description="Формат экспорта: json, csv"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Экспортировать данные клиентов"""
    try:
        customer_service = CustomerService(db)
        customers, _ = customer_service.get_customers(
            shop_id=shop_id,
            skip=0,
            limit=10000  # Экспортировать всех клиентов, но с ограничением максимального количества
        )
        
        if format == "csv":
            # Сгенерировать CSV формат
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Записать заголовки
            writer.writerow([
                "Email", "Имя", "Телефон", "Количество заказов", "Общая сумма покупок",
                "Средний чек", "Дата первого заказа", "Дата последнего заказа",
                "Статус", "Тип"
            ])
            
            # Записать данные
            for customer in customers:
                writer.writerow([
                    customer["email"],
                    customer["name"] or "",
                    customer.get("phone") or "",
                    customer["order_count"],
                    customer["total_spent"],
                    customer["avg_order_value"],
                    customer["first_order_date"].strftime("%Y-%m-%d %H:%M:%S") if customer["first_order_date"] else "",
                    customer["last_order_date"].strftime("%Y-%m-%d %H:%M:%S") if customer["last_order_date"] else "",
                    customer["status"],
                    customer["type"]
                ])
            
            content = output.getvalue()
            media_type = "text/csv"
            filename = f"customers_export_{shop_id}.csv"
            
        else:
            # Формат JSON по умолчанию
            content = json.dumps(customers, ensure_ascii=False, indent=2)
            media_type = "application/json"
            filename = f"customers_export_{shop_id}.json"
        
        return {
            "content": content,
            "filename": filename,
            "media_type": media_type,
            "customer_count": len(customers)
        }
        
    except Exception as e:
        logger.error(f"Ошибка при экспорте данных клиентов: {e}")
        raise HTTPException(status_code=500, detail="Не удалось экспортировать данные клиентов")

@router.get("/shops/{shop_id}/customers/search")
async def search_customers(
    shop_id: int = Path(..., description="ID магазина"),
    query: str = Query(..., description="Поисковый запрос"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Поиск клиентов"""
    try:
        customer_service = CustomerService(db)
        
        # Поиск по email и имени
        customers, total = customer_service.get_customers(
            shop_id=shop_id,
            skip=0,
            limit=limit,
            email=query,
            name=query
        )
        
        return {
            "customers": customers,
            "total": total,
            "query": query
        }
    except Exception as e:
        logger.error(f"Ошибка при поиске клиентов: {e}")
        raise HTTPException(status_code=500, detail="Не удалось выполнить поиск клиентов")