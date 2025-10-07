"""
数据模式
========

定义 Pydantic 数据模式，用于 API 请求和响应的数据验证。
包含用户、商品、订单、支付等所有业务实体的模式定义。

模式设计原则:
1. 使用 Pydantic 2.0 语法
2. 支持数据验证和序列化
3. 区分请求和响应模式
4. 包含完整的字段验证规则
5. 支持嵌套对象和列表
6. 提供默认值和可选字段
"""

from .user import (
    UserCreate, UserUpdate, UserResponse, UserLogin,
    MerchantCreate, MerchantUpdate, MerchantResponse,
    Token, TokenData, UserProfile
)
from .product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductList,
    ProductImageCreate, ProductImageResponse,
    ProductCategoryCreate, ProductCategoryUpdate, ProductCategoryResponse,
    ProductTagCreate, ProductTagResponse
)
from .order import (
    OrderCreate, OrderUpdate, OrderResponse, OrderList,
    OrderItemCreate, OrderItemResponse,
    OrderStatusHistoryResponse
)
from .payment import (
    PaymentCreate, PaymentResponse, PaymentList,
    PaymentRefundCreate, PaymentRefundResponse,
    PaymentMethodResponse
)
from .cart import (
    CartResponse, CartItemCreate, CartItemUpdate, CartItemResponse
)
from .address import (
    AddressCreate, AddressUpdate, AddressResponse
)
from .review import (
    ReviewCreate, ReviewUpdate, ReviewResponse,
    ReviewImageCreate, ReviewImageResponse
)
from .notification import (
    NotificationResponse, NotificationList
)
from .ai import (
    EmbeddingRequest, EmbeddingResponse,
    SearchRequest, SearchResponse,
    AIRecommendationRequest, AIRecommendationResponse
)

__all__ = [
    # 用户相关
    "UserCreate",
    "UserUpdate", 
    "UserResponse",
    "UserLogin",
    "MerchantCreate",
    "MerchantUpdate",
    "MerchantResponse",
    "Token",
    "TokenData",
    "UserProfile",
    
    # 商品相关
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "ProductList",
    "ProductImageCreate",
    "ProductImageResponse",
    "ProductCategoryCreate",
    "ProductCategoryUpdate",
    "ProductCategoryResponse",
    "ProductTagCreate",
    "ProductTagResponse",
    
    # 订单相关
    "OrderCreate",
    "OrderUpdate",
    "OrderResponse",
    "OrderList",
    "OrderItemCreate",
    "OrderItemResponse",
    "OrderStatusHistoryResponse",
    
    # 支付相关
    "PaymentCreate",
    "PaymentResponse",
    "PaymentList",
    "PaymentRefundCreate",
    "PaymentRefundResponse",
    "PaymentMethodResponse",
    
    # 购物车相关
    "CartResponse",
    "CartItemCreate",
    "CartItemUpdate",
    "CartItemResponse",
    
    # 地址相关
    "AddressCreate",
    "AddressUpdate",
    "AddressResponse",
    
    # 评价相关
    "ReviewCreate",
    "ReviewUpdate",
    "ReviewResponse",
    "ReviewImageCreate",
    "ReviewImageResponse",
    
    # 通知相关
    "NotificationResponse",
    "NotificationList",
    
    # AI 相关
    "EmbeddingRequest",
    "EmbeddingResponse",
    "SearchRequest",
    "SearchResponse",
    "AIRecommendationRequest",
    "AIRecommendationResponse",
]

