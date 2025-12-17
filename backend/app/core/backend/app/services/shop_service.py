# backend/app/services/shop_service.py (保持原样)
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime
import logging

from backend.app.models.shop import Shop, ShopMember
from backend.app.models.user import User
from backend.app.schemas.shop import ShopCreate

logger = logging.getLogger(__name__)


class ShopService:
    @staticmethod
    def create_shop(db: Session, owner_id: int, shop_data: ShopCreate) -> Shop:
        """
        Создать новый магазин (同步版本)
        
        Args:
            db: Сессия базы данных
            owner_id: ID владельца
            shop_data: Данные магазина
            
        Returns:
            Shop: Созданный магазин
        """
        # Проверить существование магазина с таким названием
        existing_shop = db.query(Shop).filter(
            Shop.name == shop_data.name,
            Shop.owner_id == owner_id
        ).first()
        
        if existing_shop:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Магазин с таким названием уже существует"
            )
        
        # Создать магазин
        shop = Shop(
            name=shop_data.name,
            description=shop_data.description,
            join_password=shop_data.join_password,
            owner_id=owner_id
        )
        
        db.add(shop)
        db.commit()
        db.refresh(shop)
        
        # Создать запись владельца
        owner_member = ShopMember(
            shop_id=shop.id,
            user_id=owner_id,
            is_admin=True,
            is_approved=True
        )
        
        db.add(owner_member)
        db.commit()
        
        logger.info(f"Создан магазин '{shop.name}' с ID {shop.id}, владелец {owner_id}")
        return shop
    
    @staticmethod
    def join_shop(db: Session, user_id: int, join_password: str) -> ShopMember:
        """
        Присоединиться к магазину
        
        Args:
            db: Сессия базы данных
            user_id: ID пользователя
            join_password: Пароль для вступления
            
        Returns:
            ShopMember: Созданная запись участника
        """
        # Найти магазин
        shop = db.query(Shop).filter(Shop.join_password == join_password).first()
        
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Магазин с таким паролем не найден"
            )
        
        # Проверить, является ли пользователь уже участником
        existing_member = db.query(ShopMember).filter(
            ShopMember.shop_id == shop.id,
            ShopMember.user_id == user_id
        ).first()
        
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Вы уже являетесь участником этого магазина"
            )
        
        # Создать запись участника (ожидает подтверждения)
        shop_member = ShopMember(
            shop_id=shop.id,
            user_id=user_id,
            role="наблюдатель",  # Только чтение по умолчанию
            is_approved=False,
            is_admin=False
        )
        
        db.add(shop_member)
        db.commit()
        db.refresh(shop_member)
        
        logger.info(f"Пользователь {user_id} запросил вступление в магазин {shop.id}")
        return shop_member
    
    @staticmethod
    def get_user_shops(db: Session, user_id: int) -> List[Shop]:
        """
        Получить все доступные пользователю магазины
        """
        # Получить магазины, которыми владеет пользователь
        owned_shops = db.query(Shop).filter(Shop.owner_id == user_id).all()
        
        # Получить магазины, в которых пользователь является участником
        member_shops = db.query(Shop).join(ShopMember).filter(
            ShopMember.user_id == user_id,
            ShopMember.is_approved == True
        ).all()
        
        # Объединить и удалить дубликаты
        all_shops = owned_shops + member_shops
        seen_ids = set()
        unique_shops = []
        
        for shop in all_shops:
            if shop.id not in seen_ids:
                seen_ids.add(shop.id)
                unique_shops.append(shop)
        
        return unique_shops
    
    @staticmethod
    def get_pending_requests(db: Session, owner_id: int) -> List[ShopMember]:
        """
        Получить ожидающие запросы на вступление
        """
        # Получить ID магазинов, принадлежащих пользователю
        owned_shop_ids = [shop.id for shop in db.query(Shop.id).filter(Shop.owner_id == owner_id).all()]
        
        if not owned_shop_ids:
            return []
        
        # Получить ожидающие запросы из этих магазинов
        pending_requests = db.query(ShopMember).filter(
            ShopMember.shop_id.in_(owned_shop_ids),
            ShopMember.is_approved == False
        ).all()
        
        return pending_requests
    
    @staticmethod
    def approve_request(db: Session, request_id: int, approve: bool, role: str = "наблюдатель") -> ShopMember:
        """
        Одобрить или отклонить запрос на вступление
        
        Args:
            db: Сессия базы данных
            request_id: ID запроса
            approve: Одобрить
            role: Назначаемая роль
            
        Returns:
            ShopMember: Обновленная запись участника
        """
        request = db.query(ShopMember).filter(ShopMember.id == request_id).first()
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Запрос не найден"
            )
        
        if approve:
            request.is_approved = True
            request.role = role
            db.commit()
            db.refresh(request)
            logger.info(f"Одобрен запрос {request_id}, назначена роль: {role}")
        else:
            db.delete(request)
            db.commit()
            logger.info(f"Отклонен запрос {request_id}")
        
        return request if approve else None
    
    @staticmethod
    def get_shop_members(db: Session, shop_id: int) -> List[ShopMember]:
        """
        Получить всех участников магазина
        """
        return db.query(ShopMember).filter(
            ShopMember.shop_id == shop_id,
            ShopMember.is_approved == True
        ).all()