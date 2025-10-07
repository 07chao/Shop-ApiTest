"""
核心模块
========

包含应用的核心配置、数据库连接、安全认证等基础功能。

模块结构:
- config.py: 应用配置管理
- database.py: 数据库连接和会话管理
- security.py: 安全认证相关功能
- exceptions.py: 自定义异常类
- middleware.py: 中间件
- logging.py: 日志配置
"""

from .config import settings, get_settings
from .database import get_db, get_async_db
from .security import get_current_user, get_current_active_user
from .exceptions import (
    FastAPIShopException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
)

__all__ = [
    "settings",
    "get_settings",
    "get_db",
    "get_async_db",
    "get_current_user",
    "get_current_active_user",
    "FastAPIShopException",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
]

