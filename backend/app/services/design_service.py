# backend/app/services/design_service.py
"""
Сервис дизайна магазина
Обрабатывает бизнес-логику дизайна магазина
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import json

from backend.app.models.shop_design import ShopDesign, HeroBanner
from backend.app.schemas.shop_design import (
    ShopDesignCreate, ShopDesignUpdate, ShopDesignResponse,
    HeroBanner as HeroBannerSchema, UploadLogoRequest,
    ThemeColor, FontFamily, LayoutStyle
)

logger = logging.getLogger(__name__)


class DesignService:
    """Сервис дизайна магазина"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_shop_design(self, shop_id: int) -> Optional[ShopDesign]:
        """Получить дизайн магазина"""
        try:
            return self.db.query(ShopDesign)\
                .filter(ShopDesign.shop_id == shop_id)\
                .first()
        except Exception as e:
            logger.error(f"Ошибка при получении дизайна магазина: {e}")
            return None
    
    def create_shop_design(self, shop_id: int, design_data: ShopDesignCreate) -> Optional[ShopDesign]:
        """Создать дизайн магазина"""
        try:
            # Проверить, существует ли уже дизайн
            existing_design = self.get_shop_design(shop_id)
            if existing_design:
                logger.warning(f"Дизайн магазина уже существует: shop_id={shop_id}")
                return self.update_shop_design(shop_id, design_data)
            
            # Подготовить данные
            design_dict = design_data.dict(exclude={'shop_id', 'hero_banners'})
            
            # Создать дизайн
            design = ShopDesign(
                shop_id=shop_id,
                **design_dict
            )
            
            # Добавить главные баннеры
            if design_data.hero_banners:
                for banner_data in design_data.hero_banners:
                    banner = HeroBanner(**banner_data.dict())
                    design.hero_banners.append(banner)
            
            self.db.add(design)
            self.db.commit()
            self.db.refresh(design)
            
            logger.info(f"Дизайн магазина успешно создан: shop_id={shop_id}")
            return design
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при создании дизайна магазина: {e}")
            return None
    
    def update_shop_design(self, shop_id: int, update_data: ShopDesignUpdate) -> Optional[ShopDesign]:
        """Обновить дизайн магазина"""
        try:
            design = self.get_shop_design(shop_id)
            if not design:
                # Если не существует, создать дизайн по умолчанию
                default_design = ShopDesignCreate(
                    shop_id=shop_id,
                    theme_color=ThemeColor.LIGHT,
                    font_family=FontFamily.DEFAULT,
                    primary_color="#4F46E5",
                    secondary_color="#10B981",
                    background_color="#FFFFFF",
                    text_color="#1F2937",
                    layout_style=LayoutStyle.GRID,
                    hero_banners=[],
                    logo_url=None,
                    favicon_url=None
                )
                return self.create_shop_design(shop_id, default_design)
            
            update_dict = update_data.dict(exclude_unset=True, exclude={'hero_banners'})
            
            # Обновить основные поля
            for field, value in update_dict.items():
                if hasattr(design, field):
                    setattr(design, field, value)
            
            # Обновить главные баннеры
            if 'hero_banners' in update_data.dict() and update_data.hero_banners is not None:
                # Очистить существующие баннеры
                design.hero_banners.clear()
                
                # Добавить новые баннеры
                for banner_data in update_data.hero_banners:
                    banner = HeroBanner(**banner_data.dict())
                    design.hero_banners.append(banner)
            
            # Обновить конфигурацию дизайна
            if 'design_config' in update_dict and update_dict['design_config']:
                if not design.design_config:
                    design.design_config = {}
                design.design_config.update(update_dict['design_config'])
            
            design.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(design)
            
            logger.info(f"Дизайн магазина успешно обновлен: shop_id={shop_id}")
            return design
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при обновлении дизайна магазина: {e}")
            return None
    
    def update_logo(self, shop_id: int, logo_request: UploadLogoRequest) -> Optional[ShopDesign]:
        """Обновить логотип магазина"""
        try:
            design = self.get_shop_design(shop_id)
            if not design:
                return None
            
            if logo_request.logo_base64:
                # Здесь можно добавить логику обработки base64 изображения
                # Например: загрузить в облачное хранилище и получить URL
                design.logo_url = "generated_url_from_base64"
            elif logo_request.logo_url:
                design.logo_url = logo_request.logo_url
            
            design.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(design)
            
            logger.info(f"Логотип магазина успешно обновлен: shop_id={shop_id}")
            return design
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при обновлении логотипа магазина: {e}")
            return None
    
    def update_favicon(self, shop_id: int, favicon_url: str) -> Optional[ShopDesign]:
        """Обновить иконку сайта"""
        try:
            design = self.get_shop_design(shop_id)
            if not design:
                return None
            
            design.favicon_url = favicon_url
            design.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(design)
            
            logger.info(f"Иконка сайта успешно обновлена: shop_id={shop_id}")
            return design
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при обновлении иконки сайта: {e}")
            return None
    
    def add_hero_banner(self, shop_id: int, banner_data: Dict[str, Any]) -> Optional[ShopDesign]:
        """Добавить главный баннер"""
        try:
            design = self.get_shop_design(shop_id)
            if not design:
                return None
            
            # Валидация данных
            banner_schema = HeroBannerSchema(**banner_data)
            
            # Создать баннер
            banner = HeroBanner(**banner_schema.dict())
            
            # Установить порядок
            if not banner.order:
                banner.order = len(design.hero_banners) + 1
            
            design.hero_banners.append(banner)
            design.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(design)
            
            logger.info(f"Главный баннер успешно добавлен: shop_id={shop_id}, title={banner.title}")
            return design
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при добавлении главного баннера: {e}")
            return None
    
    def update_hero_banner(self, shop_id: int, banner_index: int, banner_data: Dict[str, Any]) -> Optional[ShopDesign]:
        """Обновить главный баннер"""
        try:
            design = self.get_shop_design(shop_id)
            if not design or banner_index >= len(design.hero_banners):
                return None
            
            banner = design.hero_banners[banner_index]
            
            # Обновить поля
            for field, value in banner_data.items():
                if hasattr(banner, field) and value is not None:
                    setattr(banner, field, value)
            
            design.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(design)
            
            logger.info(f"Главный баннер успешно обновлен: shop_id={shop_id}, index={banner_index}")
            return design
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при обновлении главного баннера: {e}")
            return None
    
    def remove_hero_banner(self, shop_id: int, banner_index: int) -> Optional[ShopDesign]:
        """Удалить главный баннер"""
        try:
            design = self.get_shop_design(shop_id)
            if not design or banner_index >= len(design.hero_banners):
                return None
            
            # Удалить баннер
            banner = design.hero_banners.pop(banner_index)
            
            # Пересортировать оставшиеся баннеры
            for i, remaining_banner in enumerate(design.hero_banners):
                remaining_banner.order = i + 1
            
            design.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(design)
            
            logger.info(f"Главный баннер успешно удален: shop_id={shop_id}, index={banner_index}")
            return design
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при удалении главного баннера: {e}")
            return None
    
    def reorder_hero_banners(self, shop_id: int, new_order: List[int]) -> Optional[ShopDesign]:
        """Изменить порядок главных баннеров"""
        try:
            design = self.get_shop_design(shop_id)
            if not design or len(new_order) != len(design.hero_banners):
                return None
            
            # Создать отображение индексов баннеров
            banners_by_id = {i: banner for i, banner in enumerate(design.hero_banners)}
            
            # Изменить порядок
            design.hero_banners.clear()
            for new_index in new_order:
                if new_index in banners_by_id:
                    banner = banners_by_id[new_index]
                    banner.order = len(design.hero_banners) + 1
                    design.hero_banners.append(banner)
            
            design.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(design)
            
            logger.info(f"Порядок главных баннеров успешно изменен: shop_id={shop_id}")
            return design
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при изменении порядка главных баннеров: {e}")
            return None
    
    def update_design_config(self, shop_id: int, config_key: str, config_value: Any) -> Optional[ShopDesign]:
        """Обновить конфигурацию дизайна"""
        try:
            design = self.get_shop_design(shop_id)
            if not design:
                return None
            
            if not design.design_config:
                design.design_config = {}
            
            design.design_config[config_key] = config_value
            design.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(design)
            
            logger.info(f"Конфигурация дизайна успешно обновлена: shop_id={shop_id}, key={config_key}")
            return design
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при обновлении конфигурации дизайна: {e}")
            return None
    
    def reset_design(self, shop_id: int) -> Optional[ShopDesign]:
        """Сбросить дизайн магазина к значениям по умолчанию"""
        try:
            design = self.get_shop_design(shop_id)
            if not design:
                return None
            
            # Сбросить к значениям по умолчанию
            design.theme_color = ThemeColor.LIGHT
            design.font_family = FontFamily.DEFAULT
            design.primary_color = "#4F46E5"
            design.secondary_color = "#10B981"
            design.background_color = "#FFFFFF"
            design.text_color = "#1F2937"
            design.layout_style = LayoutStyle.GRID
            
            # Очистить главные баннеры
            design.hero_banners.clear()
            
            # Очистить логотип и иконку сайта
            design.logo_url = None
            design.favicon_url = None
            
            # Сбросить конфигурацию дизайна
            design.design_config = {}
            
            design.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(design)
            
            logger.info(f"Дизайн магазина успешно сброшен: shop_id={shop_id}")
            return design
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка при сбросе дизайна магазина: {e}")
            return None
    
    def to_response(self, design: ShopDesign) -> ShopDesignResponse:
        """Преобразовать в модель ответа"""
        if not design:
            return None
        
        # Преобразовать главные баннеры
        hero_banners = [
            HeroBannerSchema(
                title=banner.title,
                subtitle=banner.subtitle,
                image_url=banner.image_url,
                button_text=banner.button_text,
                button_url=banner.button_url,
                is_active=banner.is_active,
                order=banner.order
            )
            for banner in design.hero_banners
        ]
        
        return ShopDesignResponse(
            id=design.id,
            shop_id=design.shop_id,
            theme_color=design.theme_color,
            font_family=design.font_family,
            primary_color=design.primary_color,
            secondary_color=design.secondary_color,
            background_color=design.background_color,
            text_color=design.text_color,
            layout_style=design.layout_style,
            hero_banners=hero_banners,
            logo_url=design.logo_url,
            favicon_url=design.favicon_url,
            design_config=design.design_config or {},
            created_at=design.created_at,
            updated_at=design.updated_at
        )