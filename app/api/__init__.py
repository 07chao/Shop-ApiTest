"""
API 路由模块
============

定义 FastAPI 应用的所有 API 路由，按功能模块组织。
包含用户认证、商品管理、订单处理、支付集成、AI 助手等路由。

路由设计原则:
1. 按功能模块组织路由
2. 使用依赖注入进行权限控制
3. 统一的错误处理和响应格式
4. 支持 API 版本控制
5. 包含完整的 API 文档
6. 支持异步处理
"""

from fastapi import APIRouter

from .v1 import api_router as v1_router

# 创建主路由
api_router = APIRouter()

# 包含版本化路由
api_router.include_router(v1_router, prefix="/api/v1")

__all__ = ["api_router"]

