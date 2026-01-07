# backend/app/schemas/design.py
from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, Dict, Any, List
from datetime import datetime

class ShopDesignBase(BaseModel):
    """Базовая информация о дизайне магазина"""
    logo_url: Optional[str] = Field(None, max_length=500, description="URL логотипа")
    favicon_url: Optional[str] = Field(None, max_length=500, description="URL фавикона")
    banner_url: Optional[str] = Field(None, max_length=500, description="URL баннерного изображения")
    primary_color: Optional[str] = Field("#4CAF50", max_length=7, description="Основной цвет")
    secondary_color: Optional[str] = Field("#2196F3", max_length=7, description="Вторичный цвет")
    background_color: Optional[str] = Field("#FFFFFF", max_length=7, description="Цвет фона")
    text_color: Optional[str] = Field("#333333", max_length=7, description="Цвет текста")
    font_family: Optional[str] = Field("'Microsoft YaHei', Arial, sans-serif", description="Семейство шрифтов")
    hero_title: Optional[str] = Field(None, max_length=200, description="Заголовок главной страницы")
    hero_subtitle: Optional[str] = Field(None, max_length=500, description="Подзаголовок главной страницы")
    
    @validator('primary_color', 'secondary_color', 'background_color', 'text_color')
    def validate_color(cls, v):
        if v and not v.startswith('#'):
            raise ValueError('Цвет должен начинаться с символа #')
        if v and len(v) not in [4, 7]:
            raise ValueError('Неверный формат цвета')
        return v

class HeroBanner(BaseModel):
    """Главный баннер"""
    image_url: str
    title: Optional[str] = None
    subtitle: Optional[str] = None
    link_url: Optional[str] = None
    button_text: Optional[str] = None

class ShopDesignCreate(ShopDesignBase):
    """Создание дизайна магазина"""
    shop_id: int
    hero_banners: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Список главных баннеров")
    featured_products: Optional[List[int]] = Field(default_factory=list, description="Список ID рекомендуемых товаров")
    show_best_sellers: Optional[bool] = True
    show_new_arrivals: Optional[bool] = True
    about_page: Optional[str] = None
    contact_page: Optional[str] = None

class ShopDesignUpdate(BaseModel):
    """Обновление дизайна магазина"""
    logo_url: Optional[str] = Field(None, max_length=500)
    favicon_url: Optional[str] = Field(None, max_length=500)
    banner_url: Optional[str] = Field(None, max_length=500)
    primary_color: Optional[str] = Field(None, max_length=7)
    secondary_color: Optional[str] = Field(None, max_length=7)
    background_color: Optional[str] = Field(None, max_length=7)
    text_color: Optional[str] = Field(None, max_length=7)
    font_family: Optional[str] = None
    hero_title: Optional[str] = Field(None, max_length=200)
    hero_subtitle: Optional[str] = Field(None, max_length=500)
    hero_banners: Optional[List[Dict[str, Any]]] = None
    show_best_sellers: Optional[bool] = None
    show_new_arrivals: Optional[bool] = None
    featured_products: Optional[List[int]] = None
    about_page: Optional[str] = None
    contact_page: Optional[str] = None

class ShopDesignResponse(ShopDesignBase):
    """Ответ с дизайном магазина"""
    id: int
    shop_id: int
    hero_banners: List[Dict[str, Any]] = Field(default_factory=list)
    show_best_sellers: bool = True
    show_new_arrivals: bool = True
    featured_products: List[int] = Field(default_factory=list)
    about_page: Optional[str] = None
    contact_page: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UploadLogoRequest(BaseModel):
    """Запрос на загрузку логотипа"""
    image_type: str = Field("logo", description="Тип изображения: logo, favicon, banner")
    folder: str = Field("shops", description="Папка для хранения")