"""
购物车路由 (API接口层)
====================

定义购物车相关的API接口，处理HTTP请求和响应。
负责接收客户端请求，调用服务层处理业务逻辑，返回响应结果。

本文件是API接口层，负责处理HTTP请求。
它调用数据访问层(CartService)来执行业务逻辑。
不直接操作数据库或缓存，而是通过服务层进行交互。
"""

from fastapi import APIRouter, Depends
from ...core.security import require_user
# 引入数据访问层服务
from ...services.cart_service import CartService

router = APIRouter()

"""
购物车接口
=========
"""


@router.get("/")
async def get_cart(user=Depends(require_user)):
    """
    获取用户购物车信息
    
    Args:
        user: 通过依赖注入获取的当前登录用户
        
    Returns:
        dict: 购物车数据
    """
    # 创建服务实例并调用获取购物车方法
    svc = CartService()
    return await svc.get_cart(user.id)


@router.post("/")
async def set_cart(items: list[dict], user=Depends(require_user)):
    """
    设置用户购物车商品
    
    Args:
        items (list[dict]): 购物车商品列表，每个字典包含商品信息
        user: 依赖注入的用户对象，通过require_user获取当前登录用户

    Returns:
        dict: 操作结果，成功时返回{"ok": True}
    """
    # 创建购物车服务实例
    svc = CartService()
    # 调用服务层方法设置购物车商品
    await svc.set_cart(user.id, items)
    return {"ok": True}



@router.delete("/")
async def clear_cart(user=Depends(require_user)):
    """
    清空用户购物车
    
    Args:
        user: 通过依赖注入获取的当前登录用户
        
    Returns:
        dict: 操作结果，成功时返回{"ok": True}
    """
    # 创建服务实例并调用清空购物车方法
    svc = CartService()
    await svc.clear(user.id)
    return {"ok": True}