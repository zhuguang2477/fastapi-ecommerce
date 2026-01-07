# backend/app/schemas/shop_design.py
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class ThemeColor(str, Enum):
    """Перечисление цветовых тем"""
    LIGHT = "light"
    DARK = "dark"
    BLUE = "blue"
    GREEN = "green"
    RED = "red"
    PURPLE = "purple"
    CUSTOM = "custom"

class FontFamily(str, Enum):
    """Перечисление семейств шрифтов"""
    DEFAULT = "default"
    ROBOTO = "roboto"
    OPEN_SANS = "open_sans"
    MONTSERRAT = "montserrat"
    LATO = "lato"
    PLAYFAIR = "playfair"
    CUSTOM = "custom"

class LayoutStyle(str, Enum):
    """Перечисление стилей макета"""
    GRID = "grid"
    LIST = "list"
    CARD = "card"
    COMPACT = "compact"
    CUSTOM = "custom"

class ShopDesignBase(BaseModel):
    """Базовая информация о дизайне магазина"""
    theme_color: ThemeColor = Field(ThemeColor.LIGHT, description="Цветовая тема")
    font_family: FontFamily = Field(FontFamily.DEFAULT, description="Семейство шрифтов")
    primary_color: Optional[str] = Field("#4F46E5", max_length=7, description="Основной цвет (HEX)")
    secondary_color: Optional[str] = Field("#10B981", max_length=7, description="Вторичный цвет (HEX)")
    background_color: Optional[str] = Field("#FFFFFF", max_length=7, description="Цвет фона (HEX)")
    text_color: Optional[str] = Field("#1F2937", max_length=7, description="Цвет текста (HEX)")
    layout_style: LayoutStyle = Field(LayoutStyle.GRID, description="Стиль макета")
    
    @validator('primary_color', 'secondary_color', 'background_color', 'text_color')
    def validate_hex_color(cls, v):
        if v and not v.startswith('#'):
            raise ValueError('Цвет должен быть в формате HEX (начинаться с #)')
        if v and len(v) != 7:
            raise ValueError('HEX цвет должен иметь 7 символов (например, #4F46E5)')
        return v

class HeroBanner(BaseModel):
    """Герой-баннер магазина"""
    title: str = Field(..., max_length=100, description="Заголовок баннера")
    subtitle: Optional[str] = Field(None, max_length=200, description="Подзаголовок баннера")
    image_url: Optional[str] = Field(None, max_length=500, description="URL изображения баннера")
    button_text: Optional[str] = Field(None, max_length=50, description="Текст кнопки")
    button_url: Optional[str] = Field(None, max_length=500, description="URL кнопки")
    is_active: bool = Field(True, description="Активен ли баннер")
    order: int = Field(1, description="Порядок отображения")

class UploadLogoRequest(BaseModel):
    """Запрос на загрузку логотипа"""
    logo_base64: Optional[str] = Field(None, description="Логотип в формате base64")
    logo_url: Optional[str] = Field(None, max_length=500, description="URL логотипа")
    
    @validator('logo_base64', 'logo_url')
    def validate_logo_source(cls, v, values):
        if not v and not values.get('logo_url'):
            raise ValueError('Необходимо предоставить либо logo_base64, либо logo_url')
        return v

class ShopDesignCreate(ShopDesignBase):
    """Создание дизайна магазина"""
    shop_id: int = Field(..., description="ID магазина")
    hero_banners: Optional[List[HeroBanner]] = Field(default_factory=list, description="Список герой-баннеров")
    logo_url: Optional[str] = Field(None, max_length=500, description="URL логотипа")
    favicon_url: Optional[str] = Field(None, max_length=500, description="URL фавикона")

class ShopDesignUpdate(BaseModel):
    """Обновление дизайна магазина"""
    theme_color: Optional[ThemeColor] = None
    font_family: Optional[FontFamily] = None
    primary_color: Optional[str] = Field(None, max_length=7)
    secondary_color: Optional[str] = Field(None, max_length=7)
    background_color: Optional[str] = Field(None, max_length=7)
    text_color: Optional[str] = Field(None, max_length=7)
    layout_style: Optional[LayoutStyle] = None
    hero_banners: Optional[List[HeroBanner]] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    favicon_url: Optional[str] = Field(None, max_length=500)
    design_config: Optional[Dict[str, Any]] = None  # Конфигурация дизайна

class ShopDesignResponse(ShopDesignBase):
    """Ответ с дизайном магазина"""
    id: int = Field(..., description="ID дизайна")
    shop_id: int = Field(..., description="ID магазина")
    hero_banners: List[HeroBanner] = Field(default_factory=list, description="Список герой-баннеров")
    logo_url: Optional[str] = Field(None, max_length=500, description="URL логотипа")
    favicon_url: Optional[str] = Field(None, max_length=500, description="URL фавикона")
    design_config: Dict[str, Any] = Field(default_factory=dict, description="Конфигурация дизайна")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")
    
    class Config:
        from_attributes = True