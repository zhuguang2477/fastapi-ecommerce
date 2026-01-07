# backend/app/models/shop_design.py
"""
店铺设计模型
存储店铺的视觉设计和主题设置
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from backend.app.database import Base


class ShopDesign(Base):
    """Модель дизайна магазина"""
    __tablename__ = "shop_designs"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, unique=True, index=True)
    
    # 主题设置
    theme_name = Column(String(100), default="default")
    theme_version = Column(String(20), default="1.0.0")
    theme_author = Column(String(100), nullable=True)
    
    # 颜色方案
    color_scheme = Column(JSON, nullable=True, default=dict)
    # {
    #   "primary": "#4F46E5",
    #   "secondary": "#10B981",
    #   "accent": "#F59E0B",
    #   "background": "#FFFFFF",
    #   "surface": "#F9FAFB",
    #   "text_primary": "#111827",
    #   "text_secondary": "#6B7280",
    #   "error": "#EF4444",
    #   "success": "#10B981",
    #   "warning": "#F59E0B",
    #   "info": "#3B82F6"
    # }
    
    # 字体设置
    font_settings = Column(JSON, nullable=True, default=dict)
    # {
    #   "primary_font": "Inter",
    #   "secondary_font": "Roboto",
    #   "font_weights": {
    #     "light": 300,
    #     "regular": 400,
    #     "medium": 500,
    #     "bold": 700
    #   },
    #   "font_sizes": {
    #     "small": "12px",
    #     "normal": "16px",
    #     "large": "24px",
    #     "xlarge": "32px"
    #   }
    # }
    
    # 布局设置
    layout_settings = Column(JSON, nullable=True, default=dict)
    # {
    #   "layout_type": "grid",  # grid, list, masonry
    #   "columns": 3,  # 网格列数
    #   "sidebar_position": "left",  # left, right, hidden
    #   "header_type": "sticky",  # sticky, fixed, static
    #   "footer_type": "extended",  # simple, extended
    #   "container_width": "1200px",  # 容器宽度
    #   "gutter_size": "24px"  # 间距
    # }
    
    # 头部设置
    header_settings = Column(JSON, nullable=True, default=dict)
    # {
    #   "show_logo": true,
    #   "show_search": true,
    #   "show_cart": true,
    #   "show_user_menu": true,
    #   "show_navigation": true,
    #   "navigation_style": "dropdown",  # dropdown, mega, simple
    #   "sticky_header": true,
    #   "transparent_header": false,
    #   "announcement_bar": {
    #     "enabled": true,
    #     "text": "欢迎光临！新用户首单享9折优惠",
    #     "background": "#4F46E5",
    #     "text_color": "#FFFFFF"
    #   }
    # }
    
    # 页脚设置
    footer_settings = Column(JSON, nullable=True, default=dict)
    # {
    #   "show_copyright": true,
    #   "copyright_text": "© 2025 我的店铺. 保留所有权利.",
    #   "show_social_links": true,
    #   "show_newsletter": true,
    #   "footer_columns": [
    #     {"title": "关于我们", "links": [...]},
    #     {"title": "客户服务", "links": [...]},
    #     {"title": "购物指南", "links": [...]}
    #   ],
    #   "show_back_to_top": true
    # }
    
    # 首页设置
    homepage_settings = Column(JSON, nullable=True, default=dict)
    # {
    #   "hero_banner": {
    #     "enabled": true,
    #     "images": [...],
    #     "autoplay": true,
    #     "interval": 5000
    #   },
    #   "featured_products": {
    #     "enabled": true,
    #     "limit": 8,
    #     "title": "推荐商品"
    #   },
    #   "featured_categories": {
    #     "enabled": true,
    #     "limit": 6,
    #     "title": "热门分类"
    #   },
    #   "testimonials": {
    #     "enabled": false,
    #     "limit": 5
    #   },
    #   "newsletter_section": {
    #     "enabled": true,
    #     "title": "订阅我们的新闻",
    #     "description": "获取最新产品和优惠信息"
    #   }
    # }
    
    # 产品页面设置
    product_page_settings = Column(JSON, nullable=True, default=dict)
    # {
    #   "image_gallery_style": "carousel",  # carousel, grid, stacked
    #   "show_product_videos": true,
    #   "show_related_products": true,
    #   "related_products_count": 4,
    #   "show_product_reviews": true,
    #   "reviews_per_page": 10,
    #   "show_stock_status": true,
    #   "show_sku": true,
    #   "show_breadcrumbs": true,
    #   "add_to_cart_button_style": "primary",  # primary, secondary, outline
    #   "variant_selector_style": "dropdown"  # dropdown, buttons, swatches
    # }
    
    # 分类页面设置
    category_page_settings = Column(JSON, nullable=True, default=dict)
    # {
    #   "show_category_images": true,
    #   "show_category_description": true,
    #   "products_per_page": 24,
    #   "sort_options": ["latest", "price_low", "price_high", "popular"],
    #   "default_sort": "latest",
    #   "show_filters": true,
    #   "filter_sidebar_position": "left",
    #   "show_pagination": true
    # }
    
    # 购物车和结账设置
    cart_settings = Column(JSON, nullable=True, default=dict)
    # {
    #   "show_thumbnails": true,
    #   "show_product_options": true,
    #   "allow_quantity_update": true,
    #   "show_coupon_field": true,
    #   "show_cross_sell": true,
    #   "cross_sell_limit": 4,
    #   "checkout_button_text": "前往结账",
    #   "continue_shopping_text": "继续购物"
    # }
    
    # 品牌和视觉元素
    logo_url = Column(String(500), nullable=True)
    logo_alt_text = Column(String(200), nullable=True)
    favicon_url = Column(String(500), nullable=True)
    banner_images = Column(JSON, nullable=True, default=list) 
    
    # 自定义代码
    custom_css = Column(Text, nullable=True)
    custom_js = Column(Text, nullable=True)
    custom_head_html = Column(Text, nullable=True) 
    custom_footer_html = Column(Text, nullable=True) 
    
    # SEO优化
    seo_title_template = Column(String(200), nullable=True) 
    seo_description_template = Column(String(500), nullable=True) 
    seo_image_url = Column(String(500), nullable=True)
    
    # 移动端设置
    mobile_settings = Column(JSON, nullable=True, default=dict)
    # {
    #   "mobile_menu_style": "drawer",  # drawer, bottom-nav
    #   "show_mobile_search": true,
    #   "simplified_product_grid": true,
    #   "touch_friendly_buttons": true,
    #   "mobile_breakpoint": "768px"
    # }
    
    # 性能和优化
    performance_settings = Column(JSON, nullable=True, default=dict)
    # {
    #   "lazy_load_images": true,
    #   "image_optimization": true,
    #   "minify_css_js": false,
    #   "cache_static_assets": true,
    #   "cdn_enabled": false
    # }
    
    # 审计字段
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 关系
    shop = relationship("Shop", back_populates="design", uselist=False)
    updated_by = relationship("User", foreign_keys=[last_updated_by])
    
    def __repr__(self):
        return f"<ShopDesign(id={self.id}, shop_id={self.shop_id}, theme='{self.theme_name}')>"
    
    @property
    def primary_color(self) -> str:
        """获取主色调"""
        if self.color_scheme and 'primary' in self.color_scheme:
            return self.color_scheme['primary']
        return "#4F46E5"  # 默认主色调
    
    @property
    def background_color(self) -> str:
        """获取背景色"""
        if self.color_scheme and 'background' in self.color_scheme:
            return self.color_scheme['background']
        return "#FFFFFF"  # 默认白色
    
    @property
    def text_color(self) -> str:
        """获取文本颜色"""
        if self.color_scheme and 'text_primary' in self.color_scheme:
            return self.color_scheme['text_primary']
        return "#111827"  # 默认深灰色
    
    @property
    def has_custom_css(self) -> bool:
        """是否有自定义CSS"""
        return bool(self.custom_css and self.custom_css.strip())
    
    @property
    def has_custom_js(self) -> bool:
        """是否有自定义JS"""
        return bool(self.custom_js and self.custom_js.strip())
    
    @property
    def hero_banner_enabled(self) -> bool:
        """是否启用首页横幅"""
        if self.homepage_settings and 'hero_banner' in self.homepage_settings:
            return self.homepage_settings['hero_banner'].get('enabled', False)
        return False
    
    @property
    def hero_banner_images(self) -> list:
        """获取首页横幅图片"""
        if self.hero_banner_enabled:
            return self.homepage_settings['hero_banner'].get('images', [])
        return []
    
    @property
    def related_products_enabled(self) -> bool:
        """是否显示相关商品"""
        if self.product_page_settings and 'show_related_products' in self.product_page_settings:
            return self.product_page_settings['show_related_products']
        return True
    
    def get_font_family(self, font_type: str = "primary") -> str:
        """获取字体家族"""
        if self.font_settings:
            if font_type == "primary" and 'primary_font' in self.font_settings:
                return self.font_settings['primary_font']
            elif font_type == "secondary" and 'secondary_font' in self.font_settings:
                return self.font_settings['secondary_font']
        return "Inter, system-ui, sans-serif" if font_type == "primary" else "Roboto, sans-serif"
    
    def get_font_size(self, size: str = "normal") -> str:
        """获取字体大小"""
        if self.font_settings and 'font_sizes' in self.font_settings:
            return self.font_settings['font_sizes'].get(size, "16px")
        return "16px" if size == "normal" else "12px"
    
    def get_color(self, color_name: str) -> str:
        """获取指定颜色"""
        if self.color_scheme and color_name in self.color_scheme:
            return self.color_scheme[color_name]
        
        # 默认颜色映射
        default_colors = {
            "primary": "#4F46E5",
            "secondary": "#10B981",
            "background": "#FFFFFF",
            "text_primary": "#111827",
            "error": "#EF4444",
            "success": "#10B981",
            "warning": "#F59E0B"
        }
        return default_colors.get(color_name, "#000000")
    
    def to_dict(self, include_relations: bool = False) -> dict:
        """转换为字典"""
        result = {
            'id': self.id,
            'shop_id': self.shop_id,
            'theme_name': self.theme_name,
            'theme_version': self.theme_version,
            'theme_author': self.theme_author,
            'color_scheme': self.color_scheme or {},
            'font_settings': self.font_settings or {},
            'layout_settings': self.layout_settings or {},
            'header_settings': self.header_settings or {},
            'footer_settings': self.footer_settings or {},
            'homepage_settings': self.homepage_settings or {},
            'product_page_settings': self.product_page_settings or {},
            'category_page_settings': self.category_page_settings or {},
            'cart_settings': self.cart_settings or {},
            'logo_url': self.logo_url,
            'logo_alt_text': self.logo_alt_text,
            'favicon_url': self.favicon_url,
            'banner_images': self.banner_images or [],
            'custom_css': self.custom_css,
            'custom_js': self.custom_js,
            'custom_head_html': self.custom_head_html,
            'custom_footer_html': self.custom_footer_html,
            'seo_title_template': self.seo_title_template,
            'seo_description_template': self.seo_description_template,
            'seo_image_url': self.seo_image_url,
            'mobile_settings': self.mobile_settings or {},
            'performance_settings': self.performance_settings or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_updated_by': self.last_updated_by,
            'primary_color': self.primary_color,
            'background_color': self.background_color,
            'text_color': self.text_color,
            'has_custom_css': self.has_custom_css,
            'has_custom_js': self.has_custom_js,
            'hero_banner_enabled': self.hero_banner_enabled,
            'hero_banner_images': self.hero_banner_images,
            'related_products_enabled': self.related_products_enabled
        }
        
        if include_relations:
            result['shop'] = {
                'id': self.shop.id,
                'name': self.shop.name
            } if self.shop else None
            
            if self.updated_by:
                result['updated_by'] = {
                    'id': self.updated_by.id,
                    'email': self.updated_by.email,
                    'full_name': self.updated_by.full_name
                }
        
        return result
    
class HeroBanner(Base):
    """Модель главного баннера (героя)"""
    __tablename__ = "hero_banners"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    
    # 图片信息
    image_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    image_alt = Column(String(200), nullable=True)
    
    # 内容信息
    title = Column(String(200), nullable=True)
    subtitle = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    
    # 链接和按钮
    link_url = Column(String(500), nullable=True)
    button_text = Column(String(100), nullable=True)
    button_color = Column(String(20), nullable=True)
    
    # 显示设置
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    show_on_homepage = Column(Boolean, default=True)
    show_on_mobile = Column(Boolean, default=True)
    
    # 定时设置
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    
    # 审计字段
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 关系
    shop = relationship("Shop", back_populates="hero_banners")
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<HeroBanner(id={self.id}, title='{self.title}')>"
    
    @property
    def is_currently_active(self) -> bool:
        """检查横幅当前是否活跃"""
        now = datetime.utcnow()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return self.is_active
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'shop_id': self.shop_id,
            'image_url': self.image_url,
            'thumbnail_url': self.thumbnail_url,
            'image_alt': self.image_alt,
            'title': self.title,
            'subtitle': self.subtitle,
            'description': self.description,
            'link_url': self.link_url,
            'button_text': self.button_text,
            'button_color': self.button_color,
            'display_order': self.display_order,
            'is_active': self.is_active,
            'is_currently_active': self.is_currently_active,
            'show_on_homepage': self.show_on_homepage,
            'show_on_mobile': self.show_on_mobile,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }