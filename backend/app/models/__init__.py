# 导入所有模型，确保SQLAlchemy能够发现它们
from backend.app.models.user import User
from backend.app.models.otp import OTP
from backend.app.models.shop import Shop, ShopMember

# 可导出的模型列表
__all__ = ["User", "OTP", "Shop", "ShopMember"]