# backend/app/services/design.service.py
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import io

from fastapi import UploadFile

from backend.app.models.shop_settings import ShopDesign
from backend.app.models.shop import Shop
from backend.app.models.product import Product
from backend.app.schemas.design import ShopDesignCreate, ShopDesignUpdate
from backend.app.services.upload_service import UploadService

logger = logging.getLogger(__name__)

class DesignService:
    """Сервис дизайна магазина"""
    
    def __init__(self, db: Session):
        self.db = db
        self.upload_service = UploadService()
    
    def get_design(self, shop_id: int) -> Optional[ShopDesign]:
        """Получить дизайн магазина"""
        design = self.db.query(ShopDesign).filter(
            ShopDesign.shop_id == shop_id
        ).first()
        
        return design
    
    def create_or_update_design(self, shop_id: int, design_data: ShopDesignUpdate) -> ShopDesign:
        """Создать или обновить дизайн магазина"""
        try:
            # Проверить существование магазина
            shop = self.db.query(Shop).filter(Shop.id == shop_id).first()
            if not shop:
                raise ValueError(f"Магазин не существует: {shop_id}")
            
            # Найти существующий дизайн
            design = self.get_design(shop_id)
            
            if design:
                # Обновить существующий дизайн
                update_dict = design_data.dict(exclude_unset=True)
                
                # Проверить существование рекомендуемых товаров
                if 'featured_products' in update_dict:
                    featured_products = update_dict['featured_products']
                    if featured_products:
                        valid_products = self.db.query(Product).filter(
                            Product.id.in_(featured_products),
                            Product.shop_id == shop_id
                        ).all()
                        
                        if len(valid_products) != len(featured_products):
                            invalid_ids = set(featured_products) - {p.id for p in valid_products}
                            logger.warning(f"Некоторые рекомендуемые товары не существуют: {invalid_ids}")
                            # Оставить только действительные ID товаров
                            update_dict['featured_products'] = [p.id for p in valid_products]
                
                for key, value in update_dict.items():
                    setattr(design, key, value)
                
                design.updated_at = datetime.utcnow()
                logger.info(f"Обновлен дизайн магазина: {shop_id}")
            else:
                # Создать новый дизайн
                create_dict = design_data.dict(exclude_unset=True)
                
                # Проверить существование рекомендуемых товаров
                if 'featured_products' in create_dict:
                    featured_products = create_dict['featured_products']
                    if featured_products:
                        valid_products = self.db.query(Product).filter(
                            Product.id.in_(featured_products),
                            Product.shop_id == shop_id
                        ).all()
                        
                        if len(valid_products) != len(featured_products):
                            invalid_ids = set(featured_products) - {p.id for p in valid_products}
                            logger.warning(f"Некоторые рекомендуемые товары не существуют: {invalid_ids}")
                            # Оставить только действительные ID товаров
                            create_dict['featured_products'] = [p.id for p in valid_products]
                
                design = ShopDesign(
                    shop_id=shop_id,
                    **create_dict
                )
                self.db.add(design)
                logger.info(f"Создан дизайн магазина: {shop_id}")
            
            self.db.commit()
            self.db.refresh(design)
            
            return design
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка сохранения дизайна магазина: {e}")
            raise
    
    async def upload_logo(self, shop_id: int, file: UploadFile, image_type: str = "logo") -> Optional[str]:
        """Загрузить логотип или связанные изображения (асинхронный метод)"""
        try:
            # Проверить существование магазина
            shop = self.db.query(Shop).filter(Shop.id == shop_id).first()
            if not shop:
                raise ValueError(f"Магазин не существует: {shop_id}")
            
            # Загрузить изображение
            result = await self.upload_service.upload_image(
                file,
                folder="shops"
            )
            
            # Обновить соответствующее поле в дизайне магазина
            design = self.get_design(shop_id)
            if not design:
                # Если дизайн не существует, создать дизайн по умолчанию
                design = ShopDesign(shop_id=shop_id)
                self.db.add(design)
            
            # Обновить соответствующее поле в зависимости от типа изображения
            update_data = {}
            if image_type == "logo":
                update_data["logo_url"] = result.url
            elif image_type == "favicon":
                update_data["favicon_url"] = result.url
            elif image_type == "banner":
                update_data["banner_url"] = result.url
            
            # Обновить дизайн
            design = self.create_or_update_design(
                shop_id, 
                ShopDesignUpdate(**update_data)
            )
            
            logger.info(f"Загрузка {image_type} успешна: {result.url}")
            return result.url
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка загрузки логотипа: {e}")
            raise
    
    def add_hero_banner(self, shop_id: int, banner_data: Dict[str, Any]) -> bool:
        """Добавить баннер на главную страницу"""
        try:
            design = self.get_design(shop_id)
            
            if not design:
                # Если дизайн не существует, создать дизайн по умолчанию
                design = ShopDesign(shop_id=shop_id)
                self.db.add(design)
                self.db.flush()
            
            # Получить существующие баннеры или инициализировать
            hero_banners = design.hero_banners or []
            
            # Добавить новый баннер
            hero_banners.append(banner_data)
            
            # Ограничить количество баннеров (максимум 5)
            if len(hero_banners) > 5:
                hero_banners = hero_banners[-5:]
            
            design.hero_banners = hero_banners
            design.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Баннер главной страницы успешно добавлен: {shop_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка добавления баннера главной страницы: {e}")
            return False
    
    def remove_hero_banner(self, shop_id: int, banner_index: int) -> bool:
        """Удалить баннер с главной страницы"""
        try:
            design = self.get_design(shop_id)
            
            if not design or not design.hero_banners:
                return False
            
            hero_banners = design.hero_banners
            
            # Проверить допустимость индекса
            if banner_index < 0 or banner_index >= len(hero_banners):
                return False
            
            # Удалить указанный баннер
            hero_banners.pop(banner_index)
            design.hero_banners = hero_banners
            design.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Баннер главной страницы успешно удален: {shop_id}, индекс: {banner_index}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка удаления баннера главной страницы: {e}")
            return False