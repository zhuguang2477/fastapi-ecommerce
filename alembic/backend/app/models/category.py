# backend/app/models/category.py
"""
分类模型
支持多级分类结构
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, Numeric, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.database import Base


class Category(Base):
    """Модель категории"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    
    # 分类信息
    name = Column(String(100), nullable=False, index=True)
    slug = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    
    # 层级结构
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    level = Column(Integer, default=0)
    path = Column(String(500), nullable=True)
    
    # 排序和显示
    position = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    # SEO元数据
    meta_title = Column(String(200), nullable=True)
    meta_description = Column(String(500), nullable=True)
    meta_keywords = Column(String(500), nullable=True)
    
    # 统计信息
    product_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    
    # 新增字段：分类类型
    category_type = Column(String(50), default="product")
    icon_class = Column(String(100), nullable=True)
    template = Column(String(100), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    shop = relationship("Shop", back_populates="categories")
    parent = relationship("Category", remote_side=[id], backref="children")
    products = relationship("Product", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', shop_id={self.shop_id})>"
    
    @property
    def full_path(self) -> str:
        """获取完整路径"""
        if self.parent and self.parent.path:
            return f"{self.parent.path}/{self.id}"
        return str(self.id)
    
    @property
    def display_name(self) -> str:
        """获取显示名称（带缩进）"""
        indent = "  " * self.level
        return f"{indent}{self.name}"
    
    @property
    def breadcrumbs(self) -> list:
        """获取面包屑导航"""
        breadcrumbs = []
        current = self
        
        while current:
            breadcrumbs.insert(0, {
                'id': current.id,
                'name': current.name,
                'slug': current.slug,
                'level': current.level
            })
            current = current.parent
        
        return breadcrumbs
    
    @property
    def is_root(self) -> bool:
        """是否为根分类"""
        return self.parent_id is None or self.parent_id == 0
    
    @property
    def children_count(self) -> int:
        """获取子分类数量"""
        return len(self.children) if self.children else 0
    
    def get_ancestors(self):
        """获取所有祖先分类"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return list(reversed(ancestors))
    
    def get_descendants(self, include_self: bool = False):
        """获取所有后代分类"""
        from sqlalchemy.orm import Session
        
        def collect_descendants(category, descendants):
            for child in category.children:
                descendants.append(child)
                collect_descendants(child, descendants)
        
        descendants = []
        if include_self:
            descendants.append(self)
        
        collect_descendants(self, descendants)
        return descendants
    
    def update_product_count(self):
        """更新商品数量统计"""
        if self.products:
            self.product_count = len([p for p in self.products if p.status == 'PUBLISHED'])
        else:
            self.product_count = 0
        
        # 递归更新子分类
        for child in self.children:
            child.update_product_count()
    
    def to_dict(self, include_relations: bool = False, include_children: bool = False) -> dict:
        """转换为字典"""
        result = {
            'id': self.id,
            'shop_id': self.shop_id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'image_url': self.image_url,
            'parent_id': self.parent_id,
            'level': self.level,
            'path': self.path,
            'position': self.position,
            'is_active': self.is_active,
            'is_featured': self.is_featured,
            'category_type': self.category_type,
            'icon_class': self.icon_class,
            'template': self.template,
            'meta_title': self.meta_title,
            'meta_description': self.meta_description,
            'meta_keywords': self.meta_keywords,
            'product_count': self.product_count,
            'view_count': self.view_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'full_path': self.full_path,
            'display_name': self.display_name,
            'is_root': self.is_root,
            'children_count': self.children_count,
            'breadcrumbs': self.breadcrumbs
        }
        
        if include_relations:
            result['shop'] = {
                'id': self.shop.id,
                'name': self.shop.name
            } if self.shop else None
            
            if self.parent:
                result['parent'] = {
                    'id': self.parent.id,
                    'name': self.parent.name,
                    'slug': self.parent.slug
                }
        
        if include_children and self.children:
            result['children'] = [child.to_dict() for child in sorted(self.children, key=lambda x: x.position)]
        
        return result


class CategoryStats(Base):
    """Модель статистики категорий（用于缓存统计信息）"""
    __tablename__ = "category_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    
    # 统计字段
    total_products = Column(Integer, default=0)
    active_products = Column(Integer, default=0)
    total_sales = Column(Integer, default=0)
    total_revenue = Column(Numeric(10, 2), default=0)
    average_rating = Column(Numeric(3, 2), default=0)
    
    # 新增统计字段
    total_views = Column(Integer, default=0)
    conversion_rate = Column(Numeric(5, 2), default=0)
    average_price = Column(Numeric(10, 2), default=0)
    
    # 时间段
    period_type = Column(String(20), default="all_time")
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    
    # 更新时间
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    category = relationship("Category")
    
    def __repr__(self):
        return f"<CategoryStats(category_id={self.category_id}, total_products={self.total_products})>"
    
    @property
    def revenue_formatted(self) -> str:
        """格式化收入"""
        return f"¥{self.total_revenue:,.2f}"
    
    @property
    def conversion_rate_percentage(self) -> str:
        """格式化转化率"""
        return f"{self.conversion_rate:.2f}%"
    
    @property
    def average_price_formatted(self) -> str:
        """格式化平均价格"""
        return f"¥{self.average_price:,.2f}"
    
    def update_stats(self, db_session):
        """更新分类统计信息"""
        from sqlalchemy import func
        
        # 获取分类的所有商品
        category = db_session.query(Category).filter(Category.id == self.category_id).first()
        if not category:
            return
        
        # 获取所有后代分类（包括自己）
        descendants = category.get_descendants(include_self=True)
        category_ids = [c.id for c in descendants]
        
        # 导入Product模型
        from backend.app.models.product import Product
        
        # 计算统计信息
        stats = db_session.query(
            func.count(Product.id).label('total_products'),
            func.sum(Product.order_count).label('total_sales'),
            func.sum(Product.view_count).label('total_views'),
            func.avg(Product.average_rating).label('average_rating'),
            func.avg(Product.price).label('average_price')
        ).filter(
            Product.category_id.in_(category_ids),
            Product.status == 'PUBLISHED'
        ).first()
        
        if stats:
            self.total_products = stats.total_products or 0
            self.total_sales = stats.total_sales or 0
            self.total_views = stats.total_views or 0
            self.average_rating = float(stats.average_rating or 0)
            self.average_price = float(stats.average_price or 0)
            
            # 计算转化率（基于视图和销售）
            if self.total_views > 0:
                self.conversion_rate = (self.total_sales / self.total_views) * 100
    
    def to_dict(self, include_relations: bool = False) -> dict:
        """转换为字典"""
        result = {
            'id': self.id,
            'category_id': self.category_id,
            'total_products': self.total_products,
            'active_products': self.active_products,
            'total_sales': self.total_sales,
            'total_revenue': float(self.total_revenue) if self.total_revenue else 0,
            'average_rating': float(self.average_rating) if self.average_rating else 0,
            'total_views': self.total_views,
            'conversion_rate': float(self.conversion_rate) if self.conversion_rate else 0,
            'average_price': float(self.average_price) if self.average_price else 0,
            'period_type': self.period_type,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'revenue_formatted': self.revenue_formatted,
            'conversion_rate_percentage': self.conversion_rate_percentage,
            'average_price_formatted': self.average_price_formatted
        }
        
        if include_relations:
            result['category'] = {
                'id': self.category.id,
                'name': self.category.name,
                'slug': self.category.slug
            } if self.category else None
        
        return result