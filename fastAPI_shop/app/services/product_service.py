"""
商品服务
========

提供商品相关的业务逻辑处理，包括商品管理、库存处理等。
支持高并发场景下的库存扣减、分布式锁等操作。

设计思路:
1. 使用 Redis 分布式锁保证库存扣减的原子性
2. 支持库存预扣减和回滚机制
3. 集成数据库事务确保数据一致性
4. 提供库存预警和补货提醒功能
5. 支持批量操作和性能优化
"""

import asyncio
import structlog
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, update
from redis import asyncio as aioredis

from ..core.config import settings
from ..models.product import Product
from ..core.database import async_engine

# 配置日志
logger = structlog.get_logger(__name__)

# Redis 连接
redis_client = aioredis.from_url(settings.redis_url)


async def check_stock_availability(
    db: AsyncSession, 
    product_id: int, 
    quantity: int
) -> bool:
    """
    检查商品库存是否充足
    
    Args:
        db: 数据库会话
        product_id: 商品ID
        quantity: 需要的数量
        
    Returns:
        bool: 库存是否充足
    """
    try:
        # 先从Redis检查库存（快速检查）
        redis_key = f"stock:{product_id}"
        redis_stock = await redis_client.get(redis_key)
        
        if redis_stock is not None:
            # Redis中有库存信息，直接比较
            return int(redis_stock) >= quantity
        
        # Redis中没有库存信息，从数据库查询
        result = await db.execute(
            "SELECT stock FROM products WHERE id = :product_id AND is_deleted = false",
            {"product_id": product_id}
        )
        row = result.fetchone()
        
        if not row:
            return False
            
        return row[0] >= quantity
        
    except Exception as e:
        logger.error("Stock availability check error", 
                    error=str(e), 
                    product_id=product_id, 
                    quantity=quantity)
        return False


async def reserve_stock(
    db: AsyncSession, 
    product_id: int, 
    quantity: int,
    order_id: Optional[int] = None
) -> bool:
    """
    预扣库存（使用Redis分布式锁）
    
    Args:
        db: 数据库会话
        product_id: 商品ID
        quantity: 需要的数量
        order_id: 订单ID（可选）
        
    Returns:
        bool: 是否预扣成功
    """
    lock_key = f"lock:stock:{product_id}"
    lock_value = f"order:{order_id or 'unknown'}:{asyncio.get_event_loop().time()}"
    
    try:
        # 获取分布式锁（最多等待10秒，锁持有时间30秒）
        lock_acquired = await redis_client.set(
            lock_key, 
            lock_value, 
            nx=True, 
            ex=30
        )
        
        if not lock_acquired:
            logger.warning("Failed to acquire stock lock", 
                          product_id=product_id, 
                          order_id=order_id)
            return False
        
        try:
            # 从Redis获取当前库存
            redis_key = f"stock:{product_id}"
            current_stock = await redis_client.get(redis_key)
            
            if current_stock is None:
                # Redis中没有库存信息，从数据库加载
                result = await db.execute(
                    "SELECT stock FROM products WHERE id = :product_id AND is_deleted = false",
                    {"product_id": product_id}
                )
                row = result.fetchone()
                if not row:
                    return False
                
                current_stock = row[0]
                # 同步到Redis
                await redis_client.set(redis_key, current_stock)
            else:
                current_stock = int(current_stock)
            
            # 检查库存是否充足
            if current_stock < quantity:
                return False
            
            # 预扣库存（Redis中减库存）
            new_stock = current_stock - quantity
            await redis_client.set(redis_key, new_stock)
            
            # 记录预扣操作到Redis（用于后续确认或回滚）
            reserve_key = f"reserve:{product_id}:{order_id}"
            await redis_client.setex(
                reserve_key, 
                600,  # 10分钟过期
                quantity
            )
            
            logger.info("Stock reserved successfully", 
                       product_id=product_id, 
                       quantity=quantity, 
                       order_id=order_id)
            return True
            
        finally:
            # 释放锁
            lua_script = """
            if redis.call("GET", KEYS[1]) == ARGV[1] then
                return redis.call("DEL", KEYS[1])
            else
                return 0
            end
            """
            await redis_client.eval(lua_script, 1, lock_key, lock_value)
            
    except Exception as e:
        logger.error("Stock reservation error", 
                    error=str(e), 
                    product_id=product_id, 
                    quantity=quantity,
                    order_id=order_id)
        return False


async def confirm_stock_reservation(
    db: AsyncSession, 
    product_id: int, 
    quantity: int,
    order_id: int
) -> bool:
    """
    确认库存预扣（更新数据库）
    
    Args:
        db: 数据库会话
        product_id: 商品ID
        quantity: 数量
        order_id: 订单ID
        
    Returns:
        bool: 是否确认成功
    """
    try:
        # 开始数据库事务
        async with db.begin():
            # 使用数据库行级锁更新库存
            result = await db.execute(
                update(Product)
                .where(and_(
                    Product.id == product_id,
                    Product.stock >= quantity,
                    Product.is_deleted == False
                ))
                .values(
                    stock=Product.stock - quantity,
                    sales_count=Product.sales_count + quantity
                )
            )
            
            if result.rowcount == 0:
                # 库存不足或更新失败
                await rollback_stock_reservation(product_id, quantity, order_id)
                return False
            
            # 删除Redis中的预扣记录
            reserve_key = f"reserve:{product_id}:{order_id}"
            await redis_client.delete(reserve_key)
            
            logger.info("Stock reservation confirmed", 
                       product_id=product_id, 
                       quantity=quantity, 
                       order_id=order_id)
            return True
            
    except Exception as e:
        logger.error("Stock reservation confirmation error", 
                    error=str(e), 
                    product_id=product_id, 
                    quantity=quantity,
                    order_id=order_id)
        await rollback_stock_reservation(product_id, quantity, order_id)
        return False


async def rollback_stock_reservation(
    product_id: int, 
    quantity: int,
    order_id: int
) -> None:
    """
    回滚库存预扣
    
    Args:
        product_id: 商品ID
        quantity: 数量
        order_id: 订单ID
    """
    try:
        # 归还Redis中的库存
        redis_key = f"stock:{product_id}"
        await redis_client.incrby(redis_key, quantity)
        
        # 删除预扣记录
        reserve_key = f"reserve:{product_id}:{order_id}"
        await redis_client.delete(reserve_key)
        
        logger.info("Stock reservation rolled back", 
                   product_id=product_id, 
                   quantity=quantity, 
                   order_id=order_id)
                   
    except Exception as e:
        logger.error("Stock reservation rollback error", 
                    error=str(e), 
                    product_id=product_id, 
                    quantity=quantity,
                    order_id=order_id)


async def sync_stock_to_cache(
    db: AsyncSession,
    product_id: Optional[int] = None
) -> None:
    """
    同步数据库库存到Redis缓存
    
    Args:
        db: 数据库会话
        product_id: 商品ID，如果为None则同步所有商品
    """
    try:
        if product_id:
            # 同步单个商品
            result = await db.execute(
                "SELECT id, stock FROM products WHERE id = :product_id AND is_deleted = false",
                {"product_id": product_id}
            )
            rows = result.fetchall()
        else:
            # 同步所有商品（在生产环境中可能需要分批处理）
            result = await db.execute(
                "SELECT id, stock FROM products WHERE is_deleted = false"
            )
            rows = result.fetchall()
        
        # 批量更新Redis
        pipe = redis_client.pipeline()
        for row in rows:
            redis_key = f"stock:{row[0]}"
            pipe.set(redis_key, row[1])
        await pipe.execute()
        
        logger.info("Stock synced to cache", 
                   product_count=len(rows),
                   product_id=product_id)
                   
    except Exception as e:
        logger.error("Stock sync to cache error", 
                    error=str(e), 
                    product_id=product_id)


async def get_cached_stock(product_id: int) -> Optional[int]:
    """
    获取缓存中的库存数量
    
    Args:
        product_id: 商品ID
        
    Returns:
        Optional[int]: 库存数量，如果不存在返回None
    """
    try:
        redis_key = f"stock:{product_id}"
        stock = await redis_client.get(redis_key)
        return int(stock) if stock is not None else None
    except Exception as e:
        logger.error("Get cached stock error", 
                    error=str(e), 
                    product_id=product_id)
        return None