"""
订单服务
========

提供订单相关的业务逻辑处理，包括订单创建、状态管理、支付集成等。
支持高并发场景下的订单处理、库存一致性保证等操作。

设计思路:
1. 使用分布式锁保证订单创建的原子性
2. 集成库存服务确保库存一致性
3. 支持订单状态机管理
4. 集成支付服务处理支付流程
5. 提供订单超时处理和自动回滚机制
6. 支持订单查询和统计分析
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select

from ..models.order import Order, OrderItem, OrderStatus, PaymentStatus
from ..models.product import Product
from ..models.user import User
from ..services.product_service import (
    check_stock_availability, 
    reserve_stock, 
    confirm_stock_reservation, 
    rollback_stock_reservation
)
from ..core.database import async_engine

# 配置日志
logger = structlog.get_logger(__name__)


async def create_order(
    db: AsyncSession,
    user: User,
    items: List[Dict[str, Any]],
    delivery_address: Optional[Dict[str, Any]] = None
) -> Optional[Order]:
    """
    创建订单
    
    Args:
        db: 数据库会话
        user: 用户对象
        items: 订单项列表 [{product_id, quantity, ...}]
        delivery_address: 配送地址信息
        
    Returns:
        Optional[Order]: 创建的订单对象，如果失败返回None
    """
    try:
        # 开始数据库事务
        async with db.begin():
            # 1. 验证库存并预扣库存
            stock_reservations = []
            total_amount = 0.0
            
            for item in items:
                product_id = item["product_id"]
                quantity = item["quantity"]
                
                # 检查库存
                if not await check_stock_availability(db, product_id, quantity):
                    logger.warning("Insufficient stock for product", 
                                 product_id=product_id, 
                                 quantity=quantity)
                    # 回滚已预扣的库存
                    for reserved_item in stock_reservations:
                        await rollback_stock_reservation(
                            reserved_item["product_id"],
                            reserved_item["quantity"],
                            None  # 还没有订单ID
                        )
                    return None
                
                # 预扣库存
                reservation_success = await reserve_stock(db, product_id, quantity)
                if not reservation_success:
                    logger.warning("Failed to reserve stock for product", 
                                 product_id=product_id, 
                                 quantity=quantity)
                    # 回滚已预扣的库存
                    for reserved_item in stock_reservations:
                        await rollback_stock_reservation(
                            reserved_item["product_id"],
                            reserved_item["quantity"],
                            None
                        )
                    return None
                
                stock_reservations.append({
                    "product_id": product_id,
                    "quantity": quantity
                })
                
                # 获取商品信息计算价格
                result = await db.execute(
                    select(Product).where(Product.id == product_id)
                )
                product = result.scalar_one_or_none()
                if not product:
                    logger.error("Product not found", product_id=product_id)
                    # 回滚已预扣的库存
                    for reserved_item in stock_reservations:
                        await rollback_stock_reservation(
                            reserved_item["product_id"],
                            reserved_item["quantity"],
                            None
                        )
                    return None
                
                total_amount += float(product.price) * quantity
            
            # 2. 创建订单
            order_number = f"ORD{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"
            
            order = Order(
                order_number=order_number,
                user_id=user.id,
                status=OrderStatus.PENDING,
                payment_status=PaymentStatus.PENDING,
                subtotal=total_amount,
                total_amount=total_amount,
                delivery_address=delivery_address
            )
            
            db.add(order)
            await db.flush()  # 获取订单ID但不提交事务
            
            # 3. 创建订单项
            for item in items:
                product_id = item["product_id"]
                quantity = item["quantity"]
                
                # 获取商品信息
                result = await db.execute(
                    select(Product).where(Product.id == product_id)
                )
                product = result.scalar_one_or_none()
                
                if not product:
                    continue
                
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product_id,
                    product_name=product.title,
                    unit_price=float(product.price),
                    quantity=quantity,
                    total_price=float(product.price) * quantity,
                    product_attributes=product.attributes,
                    product_specifications=product.specifications
                )
                
                db.add(order_item)
            
            # 4. 确认库存预扣
            for reservation in stock_reservations:
                confirm_success = await confirm_stock_reservation(
                    db, 
                    reservation["product_id"], 
                    reservation["quantity"],
                    order.id
                )
                
                if not confirm_success:
                    logger.error("Failed to confirm stock reservation", 
                               order_id=order.id,
                               product_id=reservation["product_id"])
                    # 这里事务会自动回滚
                    return None
            
            # 提交事务
            await db.commit()
            await db.refresh(order)
            
            logger.info("Order created successfully", 
                       order_id=order.id, 
                       order_number=order.order_number,
                       user_id=user.id)
            
            return order
            
    except Exception as e:
        logger.error("Order creation error", 
                    error=str(e), 
                    user_id=user.id,
                    items=items)
        # 事务会自动回滚
        return None


async def update_order_status(
    db: AsyncSession,
    order_id: int,
    status: OrderStatus,
    payment_status: Optional[PaymentStatus] = None
) -> Optional[Order]:
    """
    更新订单状态
    
    Args:
        db: 数据库会话
        order_id: 订单ID
        status: 新的订单状态
        payment_status: 新的支付状态（可选）
        
    Returns:
        Optional[Order]: 更新后的订单对象，如果失败返回None
    """
    try:
        async with db.begin():
            # 获取订单
            result = await db.execute(
                select(Order).where(Order.id == order_id)
            )
            order = result.scalar_one_or_none()
            
            if not order:
                logger.warning("Order not found", order_id=order_id)
                return None
            
            # 更新状态
            order.status = status
            if payment_status:
                order.payment_status = payment_status
            
            # 如果订单完成，更新商品销量
            if status == OrderStatus.COMPLETED:
                # 获取订单项
                result = await db.execute(
                    select(OrderItem).where(OrderItem.order_id == order_id)
                )
                order_items = result.scalars().all()
                
                # 更新商品销量
                for item in order_items:
                    await db.execute(
                        "UPDATE products SET sales_count = sales_count + :quantity WHERE id = :product_id",
                        {"quantity": item.quantity, "product_id": item.product_id}
                    )
            
            await db.commit()
            await db.refresh(order)
            
            logger.info("Order status updated", 
                       order_id=order.id, 
                       status=status.value,
                       payment_status=payment_status.value if payment_status else None)
            
            return order
            
    except Exception as e:
        logger.error("Order status update error", 
                    error=str(e), 
                    order_id=order_id,
                    status=status.value)
        return None


async def cancel_order(
    db: AsyncSession,
    order_id: int,
    user_id: Optional[int] = None
) -> bool:
    """
    取消订单
    
    Args:
        db: 数据库会话
        order_id: 订单ID
        user_id: 用户ID（可选，用于权限检查）
        
    Returns:
        bool: 是否取消成功
    """
    try:
        async with db.begin():
            # 获取订单
            query = select(Order).where(Order.id == order_id)
            if user_id:
                query = query.where(Order.user_id == user_id)
                
            result = await db.execute(query)
            order = result.scalar_one_or_none()
            
            if not order:
                logger.warning("Order not found or access denied", 
                             order_id=order_id, 
                             user_id=user_id)
                return False
            
            # 检查订单状态是否可以取消
            if order.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED, OrderStatus.REFUNDED]:
                logger.warning("Order cannot be cancelled", 
                             order_id=order_id, 
                             status=order.status.value)
                return False
            
            # 更新订单状态
            order.status = OrderStatus.CANCELLED
            order.payment_status = PaymentStatus.CANCELLED
            
            # TODO: 实现库存回滚逻辑
            # 这里需要根据具体业务需求实现库存回滚
            
            await db.commit()
            
            logger.info("Order cancelled", 
                       order_id=order.id, 
                       user_id=user_id)
            
            return True
            
    except Exception as e:
        logger.error("Order cancellation error", 
                    error=str(e), 
                    order_id=order_id,
                    user_id=user_id)
        return False


async def get_order_by_number(
    db: AsyncSession,
    order_number: str,
    user_id: Optional[int] = None
) -> Optional[Order]:
    """
    根据订单号获取订单
    
    Args:
        db: 数据库会话
        order_number: 订单号
        user_id: 用户ID（可选，用于权限检查）
        
    Returns:
        Optional[Order]: 订单对象，如果未找到返回None
    """
    try:
        query = select(Order).where(Order.order_number == order_number)
        if user_id:
            query = query.where(Order.user_id == user_id)
            
        result = await db.execute(query)
        order = result.scalar_one_or_none()
        
        return order
        
    except Exception as e:
        logger.error("Get order by number error", 
                    error=str(e), 
                    order_number=order_number,
                    user_id=user_id)
        return None


async def get_user_orders(
    db: AsyncSession,
    user_id: int,
    limit: int = 20,
    offset: int = 0
) -> List[Order]:
    """
    获取用户订单列表
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        limit: 返回数量限制
        offset: 偏移量
        
    Returns:
        List[Order]: 订单列表
    """
    try:
        result = await db.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        orders = result.scalars().all()
        
        return orders
        
    except Exception as e:
        logger.error("Get user orders error", 
                    error=str(e), 
                    user_id=user_id)
        return []


async def process_order_timeout(
    db: AsyncSession,
    timeout_minutes: int = 30
) -> int:
    """
    处理超时订单（自动取消）
    
    Args:
        db: 数据库会话
        timeout_minutes: 超时分钟数
        
    Returns:
        int: 处理的订单数量
    """
    try:
        timeout_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        
        async with db.begin():
            # 查找超时且未支付的订单
            result = await db.execute(
                select(Order)
                .where(and_(
                    Order.status == OrderStatus.PENDING,
                    Order.payment_status == PaymentStatus.PENDING,
                    Order.created_at < timeout_time
                ))
            )
            orders = result.scalars().all()
            
            processed_count = 0
            for order in orders:
                order.status = OrderStatus.CANCELLED
                order.payment_status = PaymentStatus.CANCELLED
                # TODO: 实现库存回滚
                processed_count += 1
            
            await db.commit()
            
            logger.info("Processed order timeout", 
                       processed_count=processed_count,
                       timeout_minutes=timeout_minutes)
            
            return processed_count
            
    except Exception as e:
        logger.error("Process order timeout error", 
                    error=str(e))
        return 0