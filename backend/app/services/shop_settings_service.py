# backend/app/services/shop_settings_service.py
"""
Сервис настроек магазина
Бизнес-логика обработки настроек магазина
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from backend.app.models.shop_settings import ShopSettings
from backend.app.schemas.shop_settings import (
    ShopSettingsCreate, ShopSettingsUpdate, ShopSettingsResponse
)

logger = logging.getLogger(__name__)


class SettingsService:
    """Сервис настроек магазина"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_shop_settings(self, shop_id: int) -> Optional[ShopSettings]:
        """Получить настройки магазина"""
        try:
            return self.db.query(ShopSettings)\
                .filter(ShopSettings.shop_id == shop_id)\
                .first()
        except Exception as e:
            logger.error(f"Ошибка получения настроек магазина: {e}")
            return None
    
    def create_shop_settings(self, shop_id: int, settings_data: ShopSettingsCreate) -> Optional[ShopSettings]:
        """创建店铺设置"""
        try:
            # 检查设置是否已存在
            existing_settings = self.get_shop_settings(shop_id)
            if existing_settings:
                logger.warning(f"店铺设置已存在: shop_id={shop_id}")
                return self.update_shop_settings(shop_id, settings_data)
            
            # 创建新设置
            settings_dict = settings_data.dict(exclude={'shop_id'})
            
            # 确保JSON字段是有效的字典/列表
            json_fields = [
                'address', 'business_hours', 'order_settings', 
                'shipping_settings', 'payment_settings', 'notification_settings',
                'seo_settings', 'social_media', 'features_enabled'
            ]
            
            for field in json_fields:
                if field in settings_dict and settings_dict[field] is None:
                    # 如果是None，设置为空字典或空列表
                    if field == 'business_hours':
                        settings_dict[field] = []
                    else:
                        settings_dict[field] = {}
            
            settings = ShopSettings(
                shop_id=shop_id,
                **settings_dict
            )
            
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)
            
            logger.info(f"店铺设置成功创建: shop_id={shop_id}")
            return settings
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建店铺设置错误: {e}")
            raise
    
    def update_shop_settings(self, shop_id: int, update_data: ShopSettingsUpdate) -> Optional[ShopSettings]:
        """更新店铺设置"""
        try:
            settings = self.get_shop_settings(shop_id)
            if not settings:
                # 如果不存在，创建默认设置
                default_settings = ShopSettingsCreate(
                    shop_id=shop_id,
                    store_name=None,
                    store_email=None,
                    store_phone=None,
                    address={},
                    store_currency="RUB",
                    timezone="Europe/Moscow",
                    language="ru",
                    business_hours=[],
                    order_settings={},
                    shipping_settings={},
                    payment_settings={},
                    notification_settings={},
                    seo_settings={},
                    social_media={},
                    features_enabled={}
                )
                return self.create_shop_settings(shop_id, default_settings)
            
            update_dict = update_data.dict(exclude_unset=True)
            
            # 更新字段
            for field, value in update_dict.items():
                if hasattr(settings, field):
                    setattr(settings, field, value)
            
            settings.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(settings)
            
            logger.info(f"店铺设置成功更新: shop_id={shop_id}")
            return settings
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新店铺设置错误: {e}")
            raise
    
    def update_settings_partial(self, shop_id: int, update_data: Dict[str, Any]) -> Optional[ShopSettings]:
        """Частичное обновление настроек магазина"""
        try:
            settings = self.get_shop_settings(shop_id)
            if not settings:
                return None
            
            # Обновить базовые поля
            for field, value in update_data.items():
                if hasattr(settings, field) and field not in ['social_links', 'settings']:
                    setattr(settings, field, value)
            
            # Обновить ссылки на социальные сети
            if 'social_links' in update_data and isinstance(update_data['social_links'], dict):
                if not settings.social_links:
                    settings.social_links = {}
                settings.social_links.update(update_data['social_links'])
            
            # Обновить пользовательские настройки
            if 'settings' in update_data and isinstance(update_data['settings'], dict):
                if not settings.settings:
                    settings.settings = {}
                settings.settings.update(update_data['settings'])
            
            settings.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(settings)
            
            logger.info(f"Частичное обновление настроек магазина успешно: shop_id={shop_id}")
            return settings
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка частичного обновления настроек магазина: {e}")
            return None
    
    def update_social_links(self, shop_id: int, social_links: Dict[str, str]) -> Optional[ShopSettings]:
        """Обновить ссылки на социальные сети"""
        try:
            settings = self.get_shop_settings(shop_id)
            if not settings:
                return None
            
            if not settings.social_links:
                settings.social_links = {}
            
            settings.social_links.update(social_links)
            settings.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(settings)
            
            logger.info(f"Ссылки на социальные сети успешно обновлены: shop_id={shop_id}")
            return settings
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка обновления ссылок на социальные сети: {e}")
            return None
    
    def remove_social_link(self, shop_id: int, platform: str) -> Optional[ShopSettings]:
        """Удалить ссылку на социальную сеть"""
        try:
            settings = self.get_shop_settings(shop_id)
            if not settings or not settings.social_links:
                return None
            
            if platform in settings.social_links:
                del settings.social_links[platform]
                settings.updated_at = datetime.utcnow()
                
                self.db.commit()
                self.db.refresh(settings)
                
                logger.info(f"Ссылка на социальную сеть успешно удалена: shop_id={shop_id}, platform={platform}")
            
            return settings
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка удаления ссылки на социальную сеть: {e}")
            return None
    
    def update_custom_setting(self, shop_id: int, key: str, value: Any) -> Optional[ShopSettings]:
        """Обновить пользовательскую настройку"""
        try:
            settings = self.get_shop_settings(shop_id)
            if not settings:
                return None
            
            if not settings.settings:
                settings.settings = {}
            
            settings.settings[key] = value
            settings.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(settings)
            
            logger.info(f"Пользовательская настройка успешно обновлена: shop_id={shop_id}, key={key}")
            return settings
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка обновления пользовательской настройки: {e}")
            return None
    
    def remove_custom_setting(self, shop_id: int, key: str) -> Optional[ShopSettings]:
        """Удалить пользовательскую настройку"""
        try:
            settings = self.get_shop_settings(shop_id)
            if not settings or not settings.settings:
                return None
            
            if key in settings.settings:
                del settings.settings[key]
                settings.updated_at = datetime.utcnow()
                
                self.db.commit()
                self.db.refresh(settings)
                
                logger.info(f"Пользовательская настройка успешно удалена: shop_id={shop_id}, key={key}")
            
            return settings
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка удаления пользовательской настройки: {e}")
            return None
    
    def reset_settings(self, shop_id: int) -> Optional[ShopSettings]:
        """Сбросить настройки магазина до значений по умолчанию"""
        try:
            settings = self.get_shop_settings(shop_id)
            if not settings:
                return None
            
            # Сбросить к значениям по умолчанию
            default_settings = {
                'currency': 'RUB',
                'timezone': 'Europe/Moscow',
                'language': 'ru',
                'social_links': {},
                'settings': {}
            }
            
            for field, value in default_settings.items():
                if hasattr(settings, field):
                    setattr(settings, field, value)
            
            # Очистить необязательные поля
            optional_fields = [
                'official_name', 'contact_email', 'phone', 'address',
                'meta_title', 'meta_description', 'meta_keywords'
            ]
            
            for field in optional_fields:
                if hasattr(settings, field):
                    setattr(settings, field, None)
            
            settings.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(settings)
            
            logger.info(f"Настройки магазина успешно сброшены: shop_id={shop_id}")
            return settings
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка сброса настроек магазина: {e}")
            return None
    
    def to_response(self, settings: ShopSettings) -> ShopSettingsResponse:
        """转换为响应模型"""
        if not settings:
            return None
        
        # 从seo_settings中提取meta信息
        seo_settings = settings.seo_settings or {}
        
        return ShopSettingsResponse(
            id=settings.id,
            shop_id=settings.shop_id,
            store_name=settings.store_name,
            store_email=settings.store_email,
            store_phone=settings.store_phone,
            store_currency=settings.store_currency,
            timezone=settings.timezone,
            language=settings.language,
            address=settings.address or {},
            business_hours=settings.business_hours or [],
            order_settings=settings.order_settings or {},
            shipping_settings=settings.shipping_settings or {},
            payment_settings=settings.payment_settings or {},
            notification_settings=settings.notification_settings or {},
            seo_settings=settings.seo_settings or {},
            social_media=settings.social_media or {},
            features_enabled=settings.features_enabled or {},
            maintenance_mode=settings.maintenance_mode or False,
            maintenance_message=settings.maintenance_message,
            created_at=settings.created_at,
            updated_at=settings.updated_at
        )