"""
数据模型
========

定义应用的数据模型，使用 SQLAlchemy ORM。
包含用户、商品、订单、支付等核心业务模型。

模型设计原则:
1. 使用 SQLAlchemy 2.0 语法
2. 支持异步操作
3. 包含完整的字段验证
4. 建立合理的外键关系
5. 支持软删除和审计字段
6. 使用 JSONB 存储灵活数据
"""

from .user import User, Merchant
from .product import Product, ProductImage, ProductCategory, ProductTag
from .order import Order, OrderItem, OrderStatus
from .payment import Payment, PaymentMethod
from .cart import Cart, CartItem
from .address import Address
from .review import Review, ReviewImage
from .notification import Notification
from .ai_embedding import ProductEmbedding

__all__ = [
    # 用户相关
    "User",
    "Merchant",
    
    # 商品相关
    "Product",
    "ProductImage", 
    "ProductCategory",
    "ProductTag",
    
    # 订单相关
    "Order",
    "OrderItem",
    "OrderStatus",
    
    # 支付相关
    "Payment",
    "PaymentMethod",
    
    # 购物车相关
    "Cart",
    "CartItem",
    
    # 地址相关
    "Address",
    
    # 评价相关
    "Review",
    "ReviewImage",
    
    # 通知相关
    "Notification",
    
    # AI 相关
    "ProductEmbedding",
]

