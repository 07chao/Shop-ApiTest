"""
支付模型
========

定义支付相关的数据模型，包含支付信息、支付方式、支付历史等。
支持多种支付方式、支付状态跟踪、退款处理等功能。

设计思路:
1. 支付表存储支付基础信息
2. 支付方式表管理支持的支付方式
3. 支持支付状态流转和回调处理
4. 包含支付金额、手续费等信息
5. 支持部分退款和全额退款
6. 记录支付历史和审计信息
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, 
    ForeignKey, Enum, JSON, Index, Numeric
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum
import uuid

from ..core.database import Base


class PaymentStatus(str, enum.Enum):
    """支付状态枚举"""
    PENDING = "pending"          # 待支付
    PROCESSING = "processing"    # 支付中
    SUCCESS = "success"          # 支付成功
    FAILED = "failed"            # 支付失败
    CANCELLED = "cancelled"      # 支付取消
    REFUNDED = "refunded"        # 已退款
    PARTIALLY_REFUNDED = "partially_refunded"  # 部分退款


class PaymentMethodType(str, enum.Enum):
    """支付方式类型枚举"""
    CREDIT_CARD = "credit_card"      # 信用卡
    DEBIT_CARD = "debit_card"        # 借记卡
    BANK_TRANSFER = "bank_transfer"  # 银行转账
    DIGITAL_WALLET = "digital_wallet"  # 数字钱包
    CASH = "cash"                    # 现金
    POINTS = "points"                # 积分
    COUPON = "coupon"                # 优惠券


class Payment(Base):
    """支付模型"""
    
    __tablename__ = "payments"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 支付编号
    payment_number: Mapped[str] = mapped_column(
        String(50), 
        unique=True,
        index=True,
        nullable=False,
        comment="支付编号"
    )
    
    # 关联订单
    order_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        comment="订单ID"
    )
    
    # 支付状态
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus),
        default=PaymentStatus.PENDING,
        comment="支付状态"
    )
    
    # 支付方式
    payment_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="支付方式"
    )
    payment_method_type: Mapped[PaymentMethodType] = mapped_column(
        Enum(PaymentMethodType),
        comment="支付方式类型"
    )
    
    # 金额信息
    amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="支付金额"
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="CNY",
        comment="货币代码"
    )
    fee_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.0,
        comment="手续费"
    )
    net_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="实际到账金额"
    )
    
    # 退款信息
    refunded_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.0,
        comment="已退款金额"
    )
    refund_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="退款次数"
    )
    
    # 第三方支付信息
    gateway: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="支付网关"
    )
    gateway_transaction_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="网关交易ID"
    )
    gateway_response: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="网关响应"
    )
    
    # 支付链接和二维码
    payment_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="支付链接"
    )
    qr_code: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="支付二维码"
    )
    
    # 时间信息
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="支付过期时间"
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="支付时间"
    )
    failed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="支付失败时间"
    )
    
    # 备注信息
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="备注"
    )
    
    # 扩展信息
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="支付元数据"
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        comment="更新时间"
    )
    
    # 关系
    order: Mapped["Order"] = relationship(
        "Order", 
        back_populates="payments"
    )
    refunds: Mapped[List["PaymentRefund"]] = relationship(
        "PaymentRefund", 
        back_populates="payment",
        cascade="all, delete-orphan"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_payments_order", "order_id"),
        Index("idx_payments_status", "status"),
        Index("idx_payments_gateway", "gateway_transaction_id"),
        Index("idx_payments_created", "created_at"),
        Index("idx_payments_number", "payment_number"),
    )
    
    @property
    def is_successful(self) -> bool:
        """支付是否成功"""
        return self.status == PaymentStatus.SUCCESS
    
    @property
    def is_refunded(self) -> bool:
        """是否已退款"""
        return self.status in [PaymentStatus.REFUNDED, PaymentStatus.PARTIALLY_REFUNDED]
    
    @property
    def remaining_amount(self) -> float:
        """剩余可退款金额"""
        return float(self.amount - self.refunded_amount)
    
    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, payment_number='{self.payment_number}', status='{self.status}')>"


class PaymentRefund(Base):
    """支付退款模型"""
    
    __tablename__ = "payment_refunds"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 关联支付
    payment_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("payments.id", ondelete="CASCADE"),
        nullable=False,
        comment="支付ID"
    )
    
    # 退款编号
    refund_number: Mapped[str] = mapped_column(
        String(50), 
        unique=True,
        index=True,
        nullable=False,
        comment="退款编号"
    )
    
    # 退款信息
    amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="退款金额"
    )
    reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="退款原因"
    )
    
    # 第三方退款信息
    gateway_refund_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="网关退款ID"
    )
    gateway_response: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="网关响应"
    )
    
    # 操作信息
    operator_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        comment="操作人ID"
    )
    operator_type: Mapped[Optional[str]] = mapped_column(
        String(20),
        comment="操作人类型"
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,
        comment="创建时间"
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="处理时间"
    )
    
    # 关系
    payment: Mapped["Payment"] = relationship(
        "Payment", 
        back_populates="refunds"
    )
    operator: Mapped[Optional["User"]] = relationship(
        "User"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_payment_refunds_payment", "payment_id"),
        Index("idx_payment_refunds_number", "refund_number"),
        Index("idx_payment_refunds_created", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<PaymentRefund(id={self.id}, refund_number='{self.refund_number}', amount={self.amount})>"


class PaymentMethod(Base):
    """支付方式模型"""
    
    __tablename__ = "payment_methods"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 支付方式信息
    name: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="支付方式名称"
    )
    code: Mapped[str] = mapped_column(
        String(50), 
        unique=True,
        index=True,
        nullable=False,
        comment="支付方式代码"
    )
    type: Mapped[PaymentMethodType] = mapped_column(
        Enum(PaymentMethodType),
        nullable=False,
        comment="支付方式类型"
    )
    
    # 配置信息
    gateway: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="支付网关"
    )
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="支付配置"
    )
    
    # 状态和排序
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否激活"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="排序"
    )
    
    # 描述信息
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="描述"
    )
    icon: Mapped[Optional[str]] = mapped_column(
        String(200),
        comment="图标"
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        comment="更新时间"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_payment_methods_code", "code"),
        Index("idx_payment_methods_active", "is_active"),
        Index("idx_payment_methods_type", "type"),
    )
    
    def __repr__(self) -> str:
        return f"<PaymentMethod(id={self.id}, name='{self.name}', code='{self.code}')>"

