"""
支付服务
========

提供支付相关的业务逻辑处理，包括支付创建、回调处理、退款等。
支持多种支付方式、支付状态跟踪、安全性保证等操作。

设计思路:
1. 支持多种支付方式（模拟支付、第三方支付）
2. 使用幂等性保证支付回调的安全性
3. 集成订单服务处理支付结果
4. 支持支付超时处理和自动取消
5. 提供退款和部分退款功能
6. 集成通知服务发送支付结果通知
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.payment import Payment, PaymentStatus, PaymentMethod
from ..models.order import Order, OrderStatus, PaymentStatus as OrderPaymentStatus
from ..services.order_service import update_order_status
from ..core.config import settings

# 配置日志
logger = structlog.get_logger(__name__)


async def create_payment(
    db: AsyncSession,
    order: Order,
    payment_method: str,
    amount: float,
    currency: str = "CNY"
) -> Optional[Payment]:
    """
    创建支付记录
    
    Args:
        db: 数据库会话
        order: 订单对象
        payment_method: 支付方式
        amount: 支付金额
        currency: 货币代码
        
    Returns:
        Optional[Payment]: 支付对象，如果失败返回None
    """
    try:
        async with db.begin():
            # 生成支付编号
            payment_number = f"PMT{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"
            
            # 创建支付记录
            payment = Payment(
                payment_number=payment_number,
                order_id=order.id,
                status=PaymentStatus.PENDING,
                payment_method=payment_method,
                amount=amount,
                currency=currency,
                net_amount=amount,  # 简化处理，实际应考虑手续费
                expires_at=datetime.utcnow() + timedelta(hours=2)  # 2小时过期
            )
            
            db.add(payment)
            await db.commit()
            await db.refresh(payment)
            
            logger.info("Payment created", 
                       payment_id=payment.id, 
                       payment_number=payment.payment_number,
                       order_id=order.id,
                       amount=amount)
            
            return payment
            
    except Exception as e:
        logger.error("Payment creation error", 
                    error=str(e), 
                    order_id=order.id,
                    amount=amount)
        return None


async def process_payment(
    db: AsyncSession,
    payment_id: int,
    gateway_transaction_id: Optional[str] = None,
    gateway_response: Optional[Dict[str, Any]] = None
) -> Optional[Payment]:
    """
    处理支付（模拟支付成功）
    
    Args:
        db: 数据库会话
        payment_id: 支付ID
        gateway_transaction_id: 网关交易ID
        gateway_response: 网关响应数据
        
    Returns:
        Optional[Payment]: 更新后的支付对象，如果失败返回None
    """
    try:
        async with db.begin():
            # 获取支付记录
            result = await db.execute(
                select(Payment).where(Payment.id == payment_id)
            )
            payment = result.scalar_one_or_none()
            
            if not payment:
                logger.warning("Payment not found", payment_id=payment_id)
                return None
            
            # 检查支付状态
            if payment.status != PaymentStatus.PENDING:
                logger.warning("Payment status is not pending", 
                             payment_id=payment_id, 
                             status=payment.status.value)
                return None
            
            # 检查支付是否过期
            if payment.expires_at and datetime.utcnow() > payment.expires_at:
                payment.status = PaymentStatus.FAILED
                payment.failed_at = datetime.utcnow()
                await db.commit()
                logger.warning("Payment expired", payment_id=payment_id)
                return payment
            
            # 更新支付状态为成功
            payment.status = PaymentStatus.SUCCESS
            payment.paid_at = datetime.utcnow()
            payment.gateway_transaction_id = gateway_transaction_id
            payment.gateway_response = gateway_response
            
            # 更新订单状态
            await update_order_status(
                db, 
                payment.order_id, 
                OrderStatus.PAID,
                OrderPaymentStatus.SUCCESS
            )
            
            await db.commit()
            await db.refresh(payment)
            
            logger.info("Payment processed successfully", 
                       payment_id=payment.id, 
                       order_id=payment.order_id)
            
            return payment
            
    except Exception as e:
        logger.error("Payment processing error", 
                    error=str(e), 
                    payment_id=payment_id)
        return None


async def handle_payment_callback(
    db: AsyncSession,
    order_id: int,
    payment_data: Dict[str, Any]
) -> bool:
    """
    处理支付回调（确保幂等性）
    
    Args:
        db: 数据库会话
        order_id: 订单ID
        payment_data: 支付回调数据
        
    Returns:
        bool: 是否处理成功
    """
    try:
        # 使用幂等性键防止重复处理
        idempotency_key = f"payment_callback:{order_id}:{payment_data.get('transaction_id', '')}"
        
        # 检查是否已处理过此回调
        # 在生产环境中，这应该使用Redis等来实现
        # 这里简化处理，直接查询支付记录
        
        async with db.begin():
            # 获取订单相关的支付记录
            result = await db.execute(
                select(Payment).where(Payment.order_id == order_id)
            )
            payment = result.scalar_one_or_none()
            
            if not payment:
                logger.warning("Payment not found for order", order_id=order_id)
                return False
            
            # 检查是否已处理
            if payment.status in [PaymentStatus.SUCCESS, PaymentStatus.REFUNDED]:
                logger.info("Payment already processed", 
                           payment_id=payment.id, 
                           status=payment.status.value)
                return True
            
            # 处理支付结果
            if payment_data.get("status") == "success":
                # 支付成功
                payment.status = PaymentStatus.SUCCESS
                payment.paid_at = datetime.utcnow()
                payment.gateway_transaction_id = payment_data.get("transaction_id")
                payment.gateway_response = payment_data
                
                # 更新订单状态
                await update_order_status(
                    db, 
                    order_id, 
                    OrderStatus.PAID,
                    OrderPaymentStatus.SUCCESS
                )
                
                logger.info("Payment callback processed successfully", 
                           payment_id=payment.id, 
                           order_id=order_id)
            else:
                # 支付失败
                payment.status = PaymentStatus.FAILED
                payment.failed_at = datetime.utcnow()
                payment.gateway_response = payment_data
                
                # 更新订单状态
                await update_order_status(
                    db, 
                    order_id, 
                    OrderStatus.PENDING,
                    OrderPaymentStatus.FAILED
                )
                
                logger.info("Payment callback processed as failed", 
                           payment_id=payment.id, 
                           order_id=order_id)
            
            await db.commit()
            return True
            
    except Exception as e:
        logger.error("Payment callback handling error", 
                    error=str(e), 
                    order_id=order_id,
                    payment_data=payment_data)
        return False


async def refund_payment(
    db: AsyncSession,
    payment_id: int,
    amount: Optional[float] = None,
    reason: Optional[str] = None
) -> bool:
    """
    退款处理
    
    Args:
        db: 数据库会话
        payment_id: 支付ID
        amount: 退款金额，如果为None则全额退款
        reason: 退款原因
        
    Returns:
        bool: 是否退款成功
    """
    try:
        async with db.begin():
            # 获取支付记录
            result = await db.execute(
                select(Payment).where(Payment.id == payment_id)
            )
            payment = result.scalar_one_or_none()
            
            if not payment:
                logger.warning("Payment not found", payment_id=payment_id)
                return False
            
            # 检查支付状态
            if payment.status != PaymentStatus.SUCCESS:
                logger.warning("Payment is not successful", 
                             payment_id=payment_id, 
                             status=payment.status.value)
                return False
            
            # 计算退款金额
            if amount is None:
                # 全额退款
                refund_amount = float(payment.amount) - float(payment.refunded_amount)
            else:
                refund_amount = amount
            
            # 检查退款金额是否超过可退款金额
            remaining_amount = float(payment.amount) - float(payment.refunded_amount)
            if refund_amount > remaining_amount:
                logger.warning("Refund amount exceeds remaining amount", 
                             payment_id=payment_id, 
                             refund_amount=refund_amount,
                             remaining_amount=remaining_amount)
                return False
            
            # 更新支付状态和退款信息
            payment.refunded_amount = float(payment.refunded_amount) + refund_amount
            payment.refund_count += 1
            
            # 更新支付状态
            if refund_amount >= float(payment.amount):
                payment.status = PaymentStatus.REFUNDED
            else:
                payment.status = PaymentStatus.PARTIALLY_REFUNDED
            
            # 创建退款记录（简化处理，实际应创建单独的退款表记录）
            # 这里直接记录在日志中
            logger.info("Payment refunded", 
                       payment_id=payment_id, 
                       refund_amount=refund_amount,
                       reason=reason)
            
            # 更新订单状态
            if payment.status == PaymentStatus.REFUNDED:
                await update_order_status(
                    db, 
                    payment.order_id, 
                    OrderStatus.REFUNDED,
                    OrderPaymentStatus.REFUNDED
                )
            
            await db.commit()
            
            logger.info("Payment refund processed", 
                       payment_id=payment_id, 
                       refund_amount=refund_amount)
            
            return True
            
    except Exception as e:
        logger.error("Payment refund error", 
                    error=str(e), 
                    payment_id=payment_id,
                    amount=amount)
        return False


async def get_payment_by_number(
    db: AsyncSession,
    payment_number: str
) -> Optional[Payment]:
    """
    根据支付编号获取支付记录
    
    Args:
        db: 数据库会话
        payment_number: 支付编号
        
    Returns:
        Optional[Payment]: 支付对象，如果未找到返回None
    """
    try:
        result = await db.execute(
            select(Payment).where(Payment.payment_number == payment_number)
        )
        payment = result.scalar_one_or_none()
        
        return payment
        
    except Exception as e:
        logger.error("Get payment by number error", 
                    error=str(e), 
                    payment_number=payment_number)
        return None


async def process_payment_timeout(
    db: AsyncSession,
    timeout_minutes: int = 120
) -> int:
    """
    处理超时支付（自动标记为失败）
    
    Args:
        db: 数据库会话
        timeout_minutes: 超时分钟数
        
    Returns:
        int: 处理的支付数量
    """
    try:
        timeout_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        
        async with db.begin():
            # 查找超时且待支付的支付记录
            result = await db.execute(
                select(Payment)
                .where(Payment.status == PaymentStatus.PENDING)
                .where(Payment.created_at < timeout_time)
            )
            payments = result.scalars().all()
            
            processed_count = 0
            for payment in payments:
                payment.status = PaymentStatus.FAILED
                payment.failed_at = datetime.utcnow()
                
                # 更新订单状态
                await update_order_status(
                    db, 
                    payment.order_id, 
                    OrderStatus.PENDING,
                    OrderPaymentStatus.FAILED
                )
                
                processed_count += 1
            
            await db.commit()
            
            logger.info("Processed payment timeout", 
                       processed_count=processed_count,
                       timeout_minutes=timeout_minutes)
            
            return processed_count
            
    except Exception as e:
        logger.error("Process payment timeout error", 
                    error=str(e))
        return 0