# backend/app/services/shop_config_service.py
"""
Сервис конфигурации магазина
Обрабатывает бизнес-логику настроек и дизайна магазина
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging

from backend.app.models.shop_settings import ShopSettings
from backend.app.models.shop_design import ShopDesign
from backend.app.models.shop import Shop
from backend.app.schemas.shop_settings import ShopSettingsUpdate
from backend.app.schemas.shop_design import ShopDesignUpdate

logger = logging.getLogger(__name__)


class ShopConfigService:
    """Сервис конфигурации магазина"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ===== Методы настроек магазина =====
    
    def get_shop_settings(self, shop_id: int) -> Optional[ShopSettings]:
        """Получить настройки магазина"""
        try:
            return self.db.query(ShopSettings).filter(
                ShopSettings.shop_id == shop_id
            ).first()
        except Exception as e:
            logger.error(f"Ошибка получения настроек магазина: {e}")
            return None
    
    def create_default_settings(self, shop_id: int) -> ShopSettings:
        """Создать настройки магазина по умолчанию"""
        try:
            # Проверить существование магазина
            shop = self.db.query(Shop).filter(Shop.id == shop_id).first()
            if not shop:
                raise ValueError(f"Магазин не существует: {shop_id}")
            
            # Создать настройки по умолчанию
            default_settings = ShopSettings(
                shop_id=shop_id,
                store_name=shop.name,
                store_email="",  # нужно установить позже
                store_currency="RUB",
                timezone="Europe/Moscow",
                language="ru-RU",
                address={},
                business_hours=[
                    {"day": "monday", "open_time": "09:00", "close_time": "18:00", "is_open": True},
                    {"day": "tuesday", "open_time": "09:00", "close_time": "18:00", "is_open": True},
                    {"day": "wednesday", "open_time": "09:00", "close_time": "18:00", "is_open": True},
                    {"day": "thursday", "open_time": "09:00", "close_time": "18:00", "is_open": True},
                    {"day": "friday", "open_time": "09:00", "close_time": "18:00", "is_open": True},
                    {"day": "saturday", "open_time": "10:00", "close_time": "17:00", "is_open": True},
                    {"day": "sunday", "open_time": "10:00", "close_time": "17:00", "is_open": False}
                ],
                order_settings={
                    "minimum_order_amount": 0,
                    "order_processing_time": 24,
                    "order_hold_time": 30,
                    "enable_order_notes": True,
                    "enable_customer_notifications": True,
                    "order_confirm_method": "auto",
                    "order_number_prefix": "ORD",
                    "order_number_length": 8,
                    "enable_backorders": False,
                    "allow_order_cancellation": True,
                    "cancellation_time_limit": 60
                },
                shipping_settings={
                    "shipping_methods": [
                        {
                            "name": "Стандартная доставка",
                            "code": "standard",
                            "cost": 0,
                            "free_shipping_threshold": 3000,
                            "estimated_days": "3-5",
                            "is_active": True
                        }
                    ],
                    "shipping_zones": [],
                    "enable_shipping_calculator": True,
                    "handling_fee": 0,
                    "enable_delivery_date_selection": False,
                    "enable_delivery_time_slots": False
                },
                payment_settings={
                    "payment_methods": [
                        {
                            "name": "Банковская карта",
                            "code": "card",
                            "is_active": True,
                            "config": {}
                        },
                        {
                            "name": "СБП (Система быстрых платежей)",
                            "code": "sbp",
                            "is_active": True,
                            "config": {}
                        }
                    ],
                    "payment_capture_method": "automatic",
                    "enable_partial_payments": False,
                    "enable_invoice_generation": True,
                    "enable_payment_reminders": True,
                    "payment_due_days": 7
                },
                notification_settings={
                    "email_notifications": {
                        "new_order": True,
                        "order_shipped": True,
                        "order_delivered": True,
                        "low_stock": True,
                        "new_customer": True
                    },
                    "sms_notifications": {
                        "order_confirmation": False,
                        "order_shipped": False,
                        "order_delivered": False
                    },
                    "push_notifications": {
                        "new_order": True,
                        "new_review": True
                    },
                    "notification_templates": {}
                },
                seo_settings={
                    "meta_title": f"{shop.name} - Интернет-магазин",
                    "meta_description": f"Добро пожаловать в {shop.name}, покупайте качественные товары",
                    "meta_keywords": f"{shop.name}, онлайн-покупки, электронная коммерция",
                    "social_media_images": {},
                    "og_tags": {},
                    "twitter_cards": {},
                    "structured_data": {},
                    "sitemap_enabled": True,
                    "robots_txt": ""
                },
                social_media={},
                features_enabled={
                    "enable_reviews": True,
                    "enable_wishlist": True,
                    "enable_comparison": True,
                    "enable_gift_wrapping": True,
                    "enable_loyalty_program": False,
                    "enable_coupons": True,
                    "enable_gift_cards": True,
                    "enable_multiple_addresses": True,
                    "enable_subscriptions": False,
                    "enable_affiliate_program": False
                },
                maintenance_mode=False,
                maintenance_message=None
            )
            
            self.db.add(default_settings)
            self.db.commit()
            self.db.refresh(default_settings)
            
            logger.info(f"Созданы настройки магазина по умолчанию: shop_id={shop_id}")
            return default_settings
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка создания настроек магазина по умолчанию: {e}")
            raise
    
    def update_shop_settings(self, shop_id: int, update_data: ShopSettingsUpdate) -> Optional[ShopSettings]:
        """Обновить настройки магазина"""
        try:
            settings = self.get_shop_settings(shop_id)
            if not settings:
                # Если настройки не существуют, создать настройки по умолчанию
                settings = self.create_default_settings(shop_id)
            
            update_dict = update_data.dict(exclude_unset=True)
            
            # Обновить поля
            for field, value in update_dict.items():
                if hasattr(settings, field):
                    setattr(settings, field, value)
            
            self.db.commit()
            self.db.refresh(settings)
            
            logger.info(f"Настройки магазина обновлены: shop_id={shop_id}")
            return settings
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка обновления настроек магазина: {e}")
            return None
    
    def update_settings_partial(self, shop_id: int, update_dict: Dict[str, Any]) -> Optional[ShopSettings]:
        """Частичное обновление настроек магазина"""
        try:
            settings = self.get_shop_settings(shop_id)
            if not settings:
                # Если настройки не существуют, создать настройки по умолчанию
                settings = self.create_default_settings(shop_id)
            
            # Особенная обработка частичного обновления JSON полей
            json_fields = [
                'address', 'business_hours', 'order_settings',
                'shipping_settings', 'payment_settings',
                'notification_settings', 'seo_settings',
                'social_media', 'features_enabled'
            ]
            
            for field, value in update_dict.items():
                if hasattr(settings, field):
                    if field in json_fields and isinstance(value, dict) and isinstance(getattr(settings, field), dict):
                        # Объединить JSON словари
                        current_value = getattr(settings, field) or {}
                        current_value.update(value)
                        setattr(settings, field, current_value)
                    else:
                        setattr(settings, field, value)
            
            self.db.commit()
            self.db.refresh(settings)
            
            logger.info(f"Настройки магазина частично обновлены: shop_id={shop_id}")
            return settings
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка частичного обновления настроек магазина: {e}")
            return None
    
    def reset_settings(self, shop_id: int) -> bool:
        """Сбросить настройки магазина к значениям по умолчанию"""
        try:
            settings = self.get_shop_settings(shop_id)
            if not settings:
                return True  # Нет настроек, не нужно сбрасывать
            
            # Получить название магазина
            shop = self.db.query(Shop).filter(Shop.id == shop_id).first()
            if not shop:
                return False
            
            # Сбросить основные поля
            settings.store_name = shop.name
            settings.store_currency = "RUB"
            settings.timezone = "Europe/Moscow"
            settings.language = "ru-RU"
            settings.address = {}
            
            # Сбросить JSON поля к значениям по умолчанию
            settings.business_hours = [
                {"day": "monday", "open_time": "09:00", "close_time": "18:00", "is_open": True},
                {"day": "tuesday", "open_time": "09:00", "close_time": "18:00", "is_open": True},
                {"day": "wednesday", "open_time": "09:00", "close_time": "18:00", "is_open": True},
                {"day": "thursday", "open_time": "09:00", "close_time": "18:00", "is_open": True},
                {"day": "friday", "open_time": "09:00", "close_time": "18:00", "is_open": True},
                {"day": "saturday", "open_time": "10:00", "close_time": "17:00", "is_open": True},
                {"day": "sunday", "open_time": "10:00", "close_time": "17:00", "is_open": False}
            ]
            
            settings.order_settings = {
                "minimum_order_amount": 0,
                "order_processing_time": 24,
                "order_hold_time": 30,
                "enable_order_notes": True,
                "enable_customer_notifications": True,
                "order_confirm_method": "auto",
                "order_number_prefix": "ORD",
                "order_number_length": 8,
                "enable_backorders": False,
                "allow_order_cancellation": True,
                "cancellation_time_limit": 60
            }
            
            self.db.commit()
            
            logger.info(f"Настройки магазина сброшены: shop_id={shop_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка сброса настроек магазина: {e}")
            return False
    
    # ===== Методы дизайна магазина =====
    
    def get_shop_design(self, shop_id: int) -> Optional[ShopDesign]:
        """Получить дизайн магазина"""
        try:
            return self.db.query(ShopDesign).filter(
                ShopDesign.shop_id == shop_id
            ).first()
        except Exception as e:
            logger.error(f"Ошибка получения дизайна магазина: {e}")
            return None
    
    def create_default_design(self, shop_id: int) -> ShopDesign:
        """Создать дизайн магазина по умолчанию"""
        try:
            # Проверить существование магазина
            shop = self.db.query(Shop).filter(Shop.id == shop_id).first()
            if not shop:
                raise ValueError(f"Магазин не существует: {shop_id}")
            
            # Создать дизайн по умолчанию
            default_design = ShopDesign(
                shop_id=shop_id,
                theme_name="default",
                color_scheme={
                    "primary_color": "#4CAF50",
                    "secondary_color": "#2196F3",
                    "accent_color": "#FF9800",
                    "background_color": "#FFFFFF",
                    "text_color": "#333333",
                    "link_color": "#1976D2",
                    "success_color": "#4CAF50",
                    "warning_color": "#FF9800",
                    "error_color": "#F44336"
                },
                font_settings={
                    "primary_font": "Arial, sans-serif",
                    "secondary_font": "Georgia, serif",
                    "font_size_base": "16px",
                    "heading_font_sizes": {
                        "h1": "2.5rem",
                        "h2": "2rem",
                        "h3": "1.75rem",
                        "h4": "1.5rem",
                        "h5": "1.25rem",
                        "h6": "1rem"
                    }
                },
                layout_settings={
                    "layout_type": "grid",
                    "columns_per_row": 4,
                    "sidebar_position": "left",
                    "header_type": "sticky",
                    "footer_type": "standard",
                    "product_card_style": "standard",
                    "enable_quick_view": True,
                    "enable_lazy_loading": True
                },
                header_settings={
                    "show_logo": True,
                    "show_search": True,
                    "show_cart": True,
                    "show_user_menu": True,
                    "show_language_switcher": False,
                    "show_currency_switcher": False,
                    "navigation_style": "dropdown",
                    "sticky_header": True,
                    "header_background": "#FFFFFF",
                    "header_text_color": "#333333"
                },
                footer_settings={
                    "show_footer": True,
                    "footer_columns": 4,
                    "show_copyright": True,
                    "show_social_icons": True,
                    "show_newsletter": True,
                    "show_payment_icons": True,
                    "footer_background": "#F5F5F5",
                    "footer_text_color": "#666666",
                    "footer_links": [
                        {"title": "О нас", "url": "/about"},
                        {"title": "Контакты", "url": "/contact"},
                        {"title": "Политика конфиденциальности", "url": "/privacy"},
                        {"title": "Условия обслуживания", "url": "/terms"}
                    ]
                },
                homepage_settings={
                    "hero_section": {
                        "enabled": True,
                        "slider_type": "image",
                        "slides": [],
                        "height": "500px",
                        "overlay_color": "rgba(0,0,0,0.3)"
                    },
                    "featured_categories": {
                        "enabled": True,
                        "show_count": 6,
                        "layout": "grid"
                    },
                    "featured_products": {
                        "enabled": True,
                        "show_count": 12,
                        "layout": "carousel"
                    },
                    "promo_banners": {
                        "enabled": True,
                        "banners": []
                    },
                    "latest_news": {
                        "enabled": False,
                        "show_count": 3
                    },
                    "testimonials": {
                        "enabled": True,
                        "show_count": 5
                    }
                },
                product_page_settings={
                    "product_layout": "vertical",
                    "show_product_images": True,
                    "image_zoom_enabled": True,
                    "show_product_videos": True,
                    "show_product_description": True,
                    "show_product_attributes": True,
                    "show_product_reviews": True,
                    "show_related_products": True,
                    "show_upsell_products": True,
                    "show_stock_status": True,
                    "show_sku": True,
                    "enable_wishlist": True,
                    "enable_share_buttons": True,
                    "enable_qty_selector": True,
                    "enable_variant_swatches": True
                },
                custom_css=None,
                custom_js=None,
                logo_url=None,
                favicon_url=None,
                banner_images=[]
            )
            
            self.db.add(default_design)
            self.db.commit()
            self.db.refresh(default_design)
            
            logger.info(f"Создан дизайн магазина по умолчанию: shop_id={shop_id}")
            return default_design
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка создания дизайна магазина по умолчанию: {e}")
            raise
    
    def update_shop_design(self, shop_id: int, update_data: ShopDesignUpdate) -> Optional[ShopDesign]:
        """Обновить дизайн магазина"""
        try:
            design = self.get_shop_design(shop_id)
            if not design:
                # Если дизайн не существует, создать дизайн по умолчанию
                design = self.create_default_design(shop_id)
            
            update_dict = update_data.dict(exclude_unset=True)
            
            # Обновить поля
            for field, value in update_dict.items():
                if hasattr(design, field):
                    setattr(design, field, value)
            
            self.db.commit()
            self.db.refresh(design)
            
            logger.info(f"Дизайн магазина обновлен: shop_id={shop_id}")
            return design
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка обновления дизайна магазина: {e}")
            return None
    
    def add_hero_banner(self, shop_id: int, banner_data: Dict[str, Any]) -> bool:
        """Добавить главный баннер"""
        try:
            design = self.get_shop_design(shop_id)
            if not design:
                design = self.create_default_design(shop_id)
            
            if not design.homepage_settings:
                design.homepage_settings = {}
            
            hero_section = design.homepage_settings.get('hero_section', {})
            if not hero_section:
                hero_section = {
                    "enabled": True,
                    "slider_type": "image",
                    "slides": [],
                    "height": "500px",
                    "overlay_color": "rgba(0,0,0,0.3)"
                }
            
            slides = hero_section.get('slides', [])
            slides.append(banner_data)
            hero_section['slides'] = slides
            
            design.homepage_settings['hero_section'] = hero_section
            
            self.db.commit()
            
            logger.info(f"Главный баннер добавлен: shop_id={shop_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка добавления главного баннера: {e}")
            return False
    
    def remove_hero_banner(self, shop_id: int, banner_index: int) -> bool:
        """Удалить главный баннер"""
        try:
            design = self.get_shop_design(shop_id)
            if not design:
                return False
            
            if not design.homepage_settings:
                return False
            
            hero_section = design.homepage_settings.get('hero_section', {})
            if not hero_section:
                return False
            
            slides = hero_section.get('slides', [])
            if banner_index >= len(slides):
                return False
            
            slides.pop(banner_index)
            hero_section['slides'] = slides
            design.homepage_settings['hero_section'] = hero_section
            
            self.db.commit()
            
            logger.info(f"Главный баннер удален: shop_id={shop_id}, index={banner_index}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка удаления главного баннера: {e}")
            return False
    
    def update_logo(self, shop_id: int, logo_url: str) -> bool:
        """Обновить логотип магазина"""
        try:
            design = self.get_shop_design(shop_id)
            if not design:
                design = self.create_default_design(shop_id)
            
            design.logo_url = logo_url
            
            self.db.commit()
            
            logger.info(f"Логотип магазина обновлен: shop_id={shop_id}, logo_url={logo_url}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка обновления логотипа магазина: {e}")
            return False
    
    def update_favicon(self, shop_id: int, favicon_url: str) -> bool:
        """Обновить фавикон"""
        try:
            design = self.get_shop_design(shop_id)
            if not design:
                design = self.create_default_design(shop_id)
            
            design.favicon_url = favicon_url
            
            self.db.commit()
            
            logger.info(f"Фавикон обновлен: shop_id={shop_id}, favicon_url={favicon_url}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка обновления фавикона: {e}")
            return False
    
    def get_shop_config_summary(self, shop_id: int) -> Dict[str, Any]:
        """Получить сводку конфигурации магазина"""
        try:
            settings = self.get_shop_settings(shop_id)
            design = self.get_shop_design(shop_id)
            
            summary = {
                "shop_id": shop_id,
                "has_settings": bool(settings),
                "has_design": bool(design)
            }
            
            if settings:
                summary["store_name"] = settings.store_name
                summary["store_currency"] = settings.store_currency
                summary["maintenance_mode"] = settings.maintenance_mode
            
            if design:
                summary["theme_name"] = design.theme_name
                summary["has_logo"] = bool(design.logo_url)
                summary["has_favicon"] = bool(design.favicon_url)
            
            return summary
            
        except Exception as e:
            logger.error(f"Ошибка получения сводки конфигурации магазина: {e}")
            return {
                "shop_id": shop_id,
                "error": str(e)
            }