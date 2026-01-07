# backend/app/services/recipient_service.py
"""
Сервисный слой для получателей
Обработка бизнес-логики, связанной с получателями
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from typing import List, Optional, Dict, Any
import logging

from backend.app.models.recipient import Recipient
from backend.app.models.customer import Customer
from backend.app.schemas.recipient import RecipientCreate, RecipientUpdate

logger = logging.getLogger(__name__)


class RecipientService:
    """Сервис получателей"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_recipient(self, shop_id: int, recipient_id: int) -> Optional[Recipient]:
        """Получить одного получателя"""
        try:
            return self.db.query(Recipient).filter(
                Recipient.id == recipient_id,
                Recipient.shop_id == shop_id
            ).first()
        except Exception as e:
            logger.error(f"Ошибка получения получателя: {e}")
            return None
    
    def get_customer_recipients(
        self, 
        shop_id: int, 
        customer_id: int,
        skip: int = 0,
        limit: int = 100,
        address_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> tuple[List[Recipient], int]:
        """Получить список получателей клиента"""
        try:
            query = self.db.query(Recipient).filter(
                Recipient.shop_id == shop_id,
                Recipient.customer_id == customer_id
            )
            
            if address_type:
                query = query.filter(Recipient.address_type == address_type)
            
            if is_active is not None:
                query = query.filter(Recipient.is_active == is_active)
            
            total = query.count()
            recipients = query.order_by(
                desc(Recipient.is_default_shipping),
                desc(Recipient.is_default_billing),
                desc(Recipient.created_at)
            ).offset(skip).limit(limit).all()
            
            return recipients, total
        except Exception as e:
            logger.error(f"Ошибка получения списка получателей клиента: {e}")
            return [], 0
    
    def create_recipient(self, shop_id: int, customer_id: int, data: RecipientCreate) -> Optional[Recipient]:
        """Создать получателя"""
        try:
            # Проверить существование клиента
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id,
                Customer.shop_id == shop_id
            ).first()
            
            if not customer:
                logger.error(f"Клиент не существует: customer_id={customer_id}, shop_id={shop_id}")
                return None
            
            # Если это адрес по умолчанию, сбросить существующие адреса по умолчанию
            if data.is_default_shipping and data.address_type in ["shipping", "both"]:
                self._clear_default_shipping(shop_id, customer_id)
            
            if data.is_default_billing and data.address_type in ["billing", "both"]:
                self._clear_default_billing(shop_id, customer_id)
            
            # Создать получателя
            recipient = Recipient(
                shop_id=shop_id,
                customer_id=customer_id,
                **data.dict()
            )
            
            self.db.add(recipient)
            self.db.commit()
            self.db.refresh(recipient)
            
            logger.info(f"Получатель успешно создан: id={recipient.id}, customer_id={customer_id}")
            return recipient
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка создания получателя: {e}")
            return None
    
    def update_recipient(
        self, 
        shop_id: int, 
        recipient_id: int, 
        data: RecipientUpdate
    ) -> Optional[Recipient]:
        """Обновить получателя"""
        try:
            recipient = self.get_recipient(shop_id, recipient_id)
            if not recipient:
                return None
            
            update_data = data.dict(exclude_unset=True)
            
            # Обработка настроек адреса по умолчанию
            if 'is_default_shipping' in update_data and update_data['is_default_shipping']:
                self._clear_default_shipping(shop_id, recipient.customer_id)
            
            if 'is_default_billing' in update_data and update_data['is_default_billing']:
                self._clear_default_billing(shop_id, recipient.customer_id)
            
            # Обновление полей
            for field, value in update_data.items():
                setattr(recipient, field, value)
            
            self.db.commit()
            self.db.refresh(recipient)
            
            logger.info(f"Получатель успешно обновлен: id={recipient.id}")
            return recipient
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка обновления получателя: {e}")
            return None
    
    def delete_recipient(self, shop_id: int, recipient_id: int) -> bool:
        """Удалить получателя"""
        try:
            recipient = self.get_recipient(shop_id, recipient_id)
            if not recipient:
                return False
            
            # Проверить, есть ли заказы, связанные с этим получателем
            if recipient.orders and len(recipient.orders) > 0:
                logger.warning(f"Получатель связан с заказами, удаление невозможно: id={recipient_id}")
                return False
            
            self.db.delete(recipient)
            self.db.commit()
            
            logger.info(f"Получатель успешно удален: id={recipient_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка удаления получателя: {e}")
            return False
    
    def get_default_shipping_address(self, shop_id: int, customer_id: int) -> Optional[Recipient]:
        """Получить адрес доставки по умолчанию"""
        try:
            return self.db.query(Recipient).filter(
                Recipient.shop_id == shop_id,
                Recipient.customer_id == customer_id,
                Recipient.is_default_shipping == True,
                Recipient.is_active == True
            ).first()
        except Exception as e:
            logger.error(f"Ошибка получения адреса доставки по умолчанию: {e}")
            return None
    
    def get_default_billing_address(self, shop_id: int, customer_id: int) -> Optional[Recipient]:
        """Получить платежный адрес по умолчанию"""
        try:
            return self.db.query(Recipient).filter(
                Recipient.shop_id == shop_id,
                Recipient.customer_id == customer_id,
                Recipient.is_default_billing == True,
                Recipient.is_active == True
            ).first()
        except Exception as e:
            logger.error(f"Ошибка получения платежного адреса по умолчанию: {e}")
            return None
    
    def _clear_default_shipping(self, shop_id: int, customer_id: int):
        """Очистить существующий адрес доставки по умолчанию"""
        try:
            self.db.query(Recipient).filter(
                Recipient.shop_id == shop_id,
                Recipient.customer_id == customer_id,
                Recipient.is_default_shipping == True
            ).update({"is_default_shipping": False})
            self.db.commit()
        except Exception as e:
            logger.error(f"Ошибка очистки адреса доставки по умолчанию: {e}")
            self.db.rollback()
    
    def _clear_default_billing(self, shop_id: int, customer_id: int):
        """Очистить существующий платежный адрес по умолчанию"""
        try:
            self.db.query(Recipient).filter(
                Recipient.shop_id == shop_id,
                Recipient.customer_id == customer_id,
                Recipient.is_default_billing == True
            ).update({"is_default_billing": False})
            self.db.commit()
        except Exception as e:
            logger.error(f"Ошибка очистки платежного адреса по умолчанию: {e}")
            self.db.rollback()