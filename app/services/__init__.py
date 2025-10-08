"""
服务层
======

定义业务逻辑服务层，包含用户、商品、订单、支付、AI 等服务。
实现核心业务逻辑，与数据访问层分离。

服务设计原则:
1. 单一职责原则，每个服务专注特定业务领域
2. 依赖注入，便于测试和维护
3. 异步处理，提高性能
4. 错误处理和日志记录
5. 数据验证和业务规则
6. 缓存和性能优化
"""

from .user_service import UserService
from .merchant_service import MerchantService
from .product_service import ProductService
from .order_service import OrderService
from .payment_service import PaymentService
from .cart_service import CartService
from .address_service import AddressService
from .review_service import ReviewService
from .notification_service import NotificationService
from .email_service import EmailService
from .ai_service import AIService
from .search_service import SearchService

__all__ = [
    "UserService",
    "MerchantService",
    "ProductService",
    "OrderService",
    "PaymentService",
    "CartService",
    "AddressService",
    "ReviewService",
    "NotificationService",
    "EmailService",
    "AIService",
    "SearchService",
]

