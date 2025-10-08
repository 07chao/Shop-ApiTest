"""
API v1 路由
===========

定义 API v1 版本的所有路由，按功能模块组织。
包含认证、用户、商品、订单、支付、AI 等模块的路由。

路由组织:
- auth: 认证相关路由
- users: 用户管理路由
- merchants: 商家管理路由
- products: 商品管理路由
- orders: 订单管理路由
- payments: 支付相关路由
- cart: 购物车路由
- addresses: 地址管理路由
- reviews: 评价管理路由
- notifications: 通知管理路由
- ai: AI 助手路由
- admin: 管理员路由
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .merchants import router as merchants_router
from .products import router as products_router
from .orders import router as orders_router
from .payments import router as payments_router
from .cart import router as cart_router
from .addresses import router as addresses_router
from .reviews import router as reviews_router
from .notifications import router as notifications_router
from .ai import router as ai_router
from .admin import router as admin_router

# 创建 v1 路由
api_router = APIRouter()

# 包含各功能模块路由
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(users_router, prefix="/users", tags=["用户管理"])
api_router.include_router(merchants_router, prefix="/merchants", tags=["商家管理"])
api_router.include_router(products_router, prefix="/products", tags=["商品管理"])
api_router.include_router(orders_router, prefix="/orders", tags=["订单管理"])
api_router.include_router(payments_router, prefix="/payments", tags=["支付管理"])
api_router.include_router(cart_router, prefix="/cart", tags=["购物车"])
api_router.include_router(addresses_router, prefix="/addresses", tags=["地址管理"])
api_router.include_router(reviews_router, prefix="/reviews", tags=["评价管理"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["通知管理"])
api_router.include_router(ai_router, prefix="/ai", tags=["AI 助手"])
api_router.include_router(admin_router, prefix="/admin", tags=["管理员"])

__all__ = ["api_router"]

