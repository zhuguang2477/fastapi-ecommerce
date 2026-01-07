# backend/app/api/v1/endpoints/__init__.py
from . import auth
from . import shops
from . import products
from . import orders
from . import categories
from . import customers
from . import basket
from . import shop_settings
from . import design
from . import recipients
from . import upload
from . import profile
from . import dashboard
from . import health

__all__ = [
    "auth",
    "shops", 
    "products",
    "orders",
    "categories",
    "customers",
    "basket",
    "shop_settings",
    "design",
    "recipients",
    "upload",
    "profile",
    "dashboard",
    "health"
]