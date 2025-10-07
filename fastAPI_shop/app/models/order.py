"""
订单模型
========

定义订单相关的数据模型，包含订单信息、订单项、订单状态等。
支持订单状态流转、支付集成、配送跟踪等功能。

设计思路:
1. 订单表存储订单基础信息
2. 订单项表存储具体商品信息
3. 订单状态表记录状态变更历史
4. 支持订单取消、退款等操作
5. 包含配送和支付信息
6. 支持订单评价和反馈
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, 
    ForeignKey, Enum, JSON, Index, Numeric, BigInteger
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum
import uuid

from ..core.database import Base


class OrderStatus(str, enum.Enum):
    """订单状态枚举"""
    PENDING = "pending"          # 待支付
    PAID = "paid"               # 已支付
    CONFIRMED = "confirmed"      # 已确认
    PREPARING = "preparing"      # 准备中
    READY = "ready"             # 待取餐
    SHIPPED = "shipped"         # 已发货
    DELIVERED = "delivered"      # 已送达
    COMPLETED = "completed"      # 已完成
    CANCELLED = "cancelled"      # 已取消
    REFUNDED = "refunded"        # 已退款


class PaymentStatus(str, enum.Enum):
    """支付状态枚举"""
    PENDING = "pending"          # 待支付
    PROCESSING = "processing"    # 支付中
    SUCCESS = "success"          # 支付成功
    FAILED = "failed"            # 支付失败
    CANCELLED = "cancelled"      # 支付取消
    REFUNDED = "refunded"        # 已退款


class DeliveryStatus(str, enum.Enum):
    """配送状态枚举"""
    PENDING = "pending"          # 待配送
    ASSIGNED = "assigned"        # 已分配
    PICKED_UP = "picked_up"      # 已取货
    IN_TRANSIT = "in_transit"    # 配送中
    DELIVERED = "delivered"      # 已送达
    FAILED = "failed"            # 配送失败


class Order(Base):
    """订单模型"""
    
    __tablename__ = "orders"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 订单编号
    order_number: Mapped[str] = mapped_column(
        String(50), 
        unique=True,
        index=True,
        nullable=False,
        comment="订单编号"
    )
    
    # 关联用户
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID"
    )
    
    # 订单状态
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus),
        default=OrderStatus.PENDING,
        comment="订单状态"
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus),
        default=PaymentStatus.PENDING,
        comment="支付状态"
    )
    delivery_status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus),
        default=DeliveryStatus.PENDING,
        comment="配送状态"
    )
    
    # 价格信息
    subtotal: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="商品小计"
    )
    tax_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.0,
        comment="税费"
    )
    shipping_fee: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.0,
        comment="配送费"
    )
    discount_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.0,
        comment="折扣金额"
    )
    total_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="订单总额"
    )
    
    # 配送信息
    delivery_address: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="配送地址"
    )
    delivery_instructions: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="配送说明"
    )
    estimated_delivery_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="预计送达时间"
    )
    actual_delivery_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="实际送达时间"
    )
    
    # 支付信息
    payment_method: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="支付方式"
    )
    payment_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="支付参考号"
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="支付时间"
    )
    
    # 商家信息
    merchant_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("merchants.id"),
        comment="商家ID"
    )
    merchant_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        comment="商家名称"
    )
    
    # 备注信息
    customer_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="客户备注"
    )
    admin_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="管理员备注"
    )
    
    # 扩展信息
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="订单元数据"
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
    user: Mapped["User"] = relationship(
        "User", 
        back_populates="orders"
    )
    merchant: Mapped[Optional["Merchant"]] = relationship(
        "Merchant"
    )
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", 
        back_populates="order",
        cascade="all, delete-orphan"
    )
    status_history: Mapped[List["OrderStatusHistory"]] = relationship(
        "OrderStatusHistory", 
        back_populates="order",
        cascade="all, delete-orphan"
    )
    payments: Mapped[List["Payment"]] = relationship(
        "Payment", 
        back_populates="order"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_orders_user", "user_id"),
        Index("idx_orders_merchant", "merchant_id"),
        Index("idx_orders_status", "status"),
        Index("idx_orders_payment_status", "payment_status"),
        Index("idx_orders_created", "created_at"),
        Index("idx_orders_number", "order_number"),
    )
    
    @property
    def is_paid(self) -> bool:
        """是否已支付"""
        return self.payment_status == PaymentStatus.SUCCESS
    
    @property
    def is_cancelled(self) -> bool:
        """是否已取消"""
        return self.status in [OrderStatus.CANCELLED, OrderStatus.REFUNDED]
    
    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.status == OrderStatus.COMPLETED
    
    def __repr__(self) -> str:
        return f"<Order(id={self.id}, order_number='{self.order_number}', status='{self.status}')>"


class OrderItem(Base):
    """订单项模型"""
    
    __tablename__ = "order_items"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 关联订单
    order_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        comment="订单ID"
    )
    
    # 关联商品
    product_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("products.id"),
        nullable=False,
        comment="商品ID"
    )
    
    # 商品信息快照
    product_name: Mapped[str] = mapped_column(
        String(200), 
        nullable=False,
        comment="商品名称"
    )
    product_sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="商品SKU"
    )
    product_image: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="商品图片"
    )
    
    # 价格和数量
    unit_price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="单价"
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="数量"
    )
    total_price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="小计"
    )
    
    # 商品属性
    product_attributes: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="商品属性快照"
    )
    product_specifications: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="商品规格快照"
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,
        comment="创建时间"
    )
    
    # 关系
    order: Mapped["Order"] = relationship(
        "Order", 
        back_populates="items"
    )
    product: Mapped["Product"] = relationship(
        "Product", 
        back_populates="order_items"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_order_items_order", "order_id"),
        Index("idx_order_items_product", "product_id"),
    )
    
    def __repr__(self) -> str:
        return f"<OrderItem(id={self.id}, product_name='{self.product_name}', quantity={self.quantity})>"


class OrderStatusHistory(Base):
    """订单状态历史模型"""
    
    __tablename__ = "order_status_history"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 关联订单
    order_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        comment="订单ID"
    )
    
    # 状态信息
    from_status: Mapped[Optional[OrderStatus]] = mapped_column(
        Enum(OrderStatus),
        comment="原状态"
    )
    to_status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus),
        nullable=False,
        comment="新状态"
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
    reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="状态变更原因"
    )
    
    # 备注
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="备注"
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,
        comment="创建时间"
    )
    
    # 关系
    order: Mapped["Order"] = relationship(
        "Order", 
        back_populates="status_history"
    )
    operator: Mapped[Optional["User"]] = relationship(
        "User"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_order_status_history_order", "order_id"),
        Index("idx_order_status_history_created", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<OrderStatusHistory(id={self.id}, order_id={self.order_id}, from_status='{self.from_status}', to_status='{self.to_status}')>"

