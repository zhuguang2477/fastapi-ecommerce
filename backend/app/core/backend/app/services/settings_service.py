# backend/app/services/setting_service.py
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from backend.app.models.shop_settings import ShopSettings
from backend.app.models.shop import Shop
from backend.app.schemas.settings import ShopSettingsCreate, ShopSettingsUpdate

logger = logging.getLogger(__name__)

class SettingsService:
    """Сервис настроек магазина"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_settings(self, shop_id: int) -> Optional[ShopSettings]:
        """Получить настройки магазина"""
        settings = self.db.query(ShopSettings).filter(
            ShopSettings.shop_id == shop_id
        ).first()
        
        return settings
    
    def create_or_update_settings(self, shop_id: int, settings_data: ShopSettingsUpdate) -> ShopSettings:
        """Создать или обновить настройки магазина"""
        try:
            # Проверить существование магазина
            shop = self.db.query(Shop).filter(Shop.id == shop_id).first()
            if not shop:
                raise ValueError(f"Магазин не существует: {shop_id}")
            
            # Найти существующие настройки
            settings = self.get_settings(shop_id)
            
            if settings:
                # Обновить существующие настройки
                update_dict = settings_data.dict(exclude_unset=True)
                
                for key, value in update_dict.items():
                    setattr(settings, key, value)
                
                settings.updated_at = datetime.utcnow()
                logger.info(f"Обновление настроек магазина: {shop_id}")
            else:
                # Создать новые настройки
                settings = ShopSettings(
                    shop_id=shop_id,
                    **settings_data.dict(exclude_unset=True)
                )
                self.db.add(settings)
                logger.info(f"Создание настроек магазина: {shop_id}")
            
            self.db.commit()
            self.db.refresh(settings)
            
            return settings
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Не удалось сохранить настройки магазина: {e}")
            raise
    
    def update_settings_partial(self, shop_id: int, update_data: Dict[str, Any]) -> Optional[ShopSettings]:
        """Частичное обновление настроек магазина"""
        try:
            settings = self.get_settings(shop_id)
            
            if not settings:
                # Если настройки не существуют, создать настройки по умолчанию
                settings = ShopSettings(shop_id=shop_id)
                self.db.add(settings)
                self.db.flush()
            
            # Обновить настройки
            for key, value in update_data.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
            
            settings.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(settings)
            
            return settings
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Не удалось частично обновить настройки магазина: {e}")
            raise
    
    def reset_settings(self, shop_id: int) -> bool:
        """Сбросить настройки магазина к значениям по умолчанию"""
        try:
            settings = self.get_settings(shop_id)
            
            if not settings:
                return True  # Если настроек нет, сброс не требуется
            
            # Сбросить к значениям по умолчанию
            defaults = {
                'official_name': None,
                'contact_email': None,
                'phone': None,
                'address': None,
                'currency': 'RUB',  # Изменено с CNY на RUB для российского контекста
                'timezone': 'Europe/Moscow',  # Изменено с Asia/Shanghai на Europe/Moscow
                'language': 'ru_RU',  # Изменено с zh_CN на ru_RU
                'meta_title': None,
                'meta_description': None,
                'meta_keywords': None,
                'social_links': {},
                'settings': {}
            }
            
            for key, value in defaults.items():
                setattr(settings, key, value)
            
            settings.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Сброс настроек магазина: {shop_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Не удалось сбросить настройки магазина: {e}")
            return False