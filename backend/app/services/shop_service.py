# backend/app/services/shop_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime

from backend.app.models.shop import Shop, ShopMember
from backend.app.models.user import User
from backend.app.schemas.shop import ShopCreate
import logging

logger = logging.getLogger(__name__)


class ShopService:
    @staticmethod
    def create_shop(db: Session, owner_id: int, shop_data: ShopCreate) -> Shop:
        """
        Создать новый магазин
        
        Args:
            db: Сеанс базы данных
            owner_id: Идентификатор владельца
            shop_data: Данные магазина
            
        Returns:
            Shop: Созданный магазин
        """
        # Проверьте, существует ли название магазина.
        existing_shop = db.query(Shop).filter(
            Shop.name == shop_data.name,
            Shop.owner_id == owner_id
        ).first()
        
        if existing_shop:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shop with this name already exists"
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
            role="owner",
            is_approved=True
        )
        
        db.add(owner_member)
        db.commit()
        
        logger.info(f"Created shop '{shop.name}' with ID {shop.id}, owner {owner_id}")
        return shop
    
    @staticmethod
    def join_shop(db: Session, user_id: int, join_password: str) -> ShopMember:
        """
        Присоединяйтесь к магазинам
        
        Args:
            db: Сеанс базы данных
            user_id: Идентификатор пользователя
            join_password: Добавить пароль
            
        Returns:
            ShopMember: Созданные записи членов
        """
        # Искать магазин
        shop = db.query(Shop).filter(Shop.join_password == join_password).first()
        
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shop not found with this password"
            )
        
        # Проверьте, является ли он членом
        existing_member = db.query(ShopMember).filter(
            ShopMember.shop_id == shop.id,
            ShopMember.user_id == user_id
        ).first()
        
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are already a member of this shop"
            )
        
        # Создание записей членов (в ожидании одобрения)
        shop_member = ShopMember(
            shop_id=shop.id,
            user_id=user_id,
            role="viewer",  # Права только для чтения по умолчанию
            is_approved=False
        )
        
        db.add(shop_member)
        db.commit()
        db.refresh(shop_member)
        
        logger.info(f"User {user_id} requested to join shop {shop.id}")
        return shop_member
    
    @staticmethod
    def get_user_shops(db: Session, user_id: int) -> List[Shop]:
        """
        Получите доступ ко всем магазинам пользователя
        """
        # Купить магазин, принадлежащий пользователю
        owned_shops = db.query(Shop).filter(Shop.owner_id == user_id).all()
        
        # Приобретение магазинов, в которых пользователи являются членами
        member_shops = db.query(Shop).join(ShopMember).filter(
            ShopMember.user_id == user_id,
            ShopMember.is_approved == True
        ).all()
        
        # Объединить и сбросить вес
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
        Получение нерассмотренных просьб о присоединении
        """
        # Получение идентификатора магазина, принадлежащего пользователю
        owned_shop_ids = [shop.id for shop in db.query(Shop.id).filter(Shop.owner_id == owner_id).all()]
        
        if not owned_shop_ids:
            return []
        
        # Получение необработанных запросов из этих магазинов
        pending_requests = db.query(ShopMember).filter(
            ShopMember.shop_id.in_(owned_shop_ids),
            ShopMember.is_approved == False
        ).all()
        
        return pending_requests
    
    @staticmethod
    def approve_request(db: Session, request_id: int, approve: bool, role: str = "viewer") -> ShopMember:
        """
        Ратификация или отклонение просьб о присоединении
        
        Args:
            db: Сеанс базы данных
            request_id: Запрос ID
            approve: Ратификация
            role: Распределенные роли
            
        Returns:
            ShopMember: Обновленный список участников
        """
        request = db.query(ShopMember).filter(ShopMember.id == request_id).first()
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found"
            )
        
        if approve:
            request.is_approved = True
            request.role = role
            db.commit()
            db.refresh(request)
            logger.info(f"Approved request {request_id}, assigned role: {role}")
        else:
            db.delete(request)
            db.commit()
            logger.info(f"Rejected request {request_id}")
        
        return request if approve else None
    
    @staticmethod
    def get_shop_members(db: Session, shop_id: int) -> List[ShopMember]:
        """
        Получить всех членов магазина
        """
        return db.query(ShopMember).filter(
            ShopMember.shop_id == shop_id,
            ShopMember.is_approved == True
        ).all()