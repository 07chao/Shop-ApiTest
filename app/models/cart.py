"""
购物车模型 (数据模型层)
=====================

定义购物车相关的数据模型，包含购物车、购物车项等。
支持购物车持久化、价格计算、库存检查等功能。

设计思路:
1. 购物车表存储用户购物车基础信息
2. 购物车项表存储具体商品信息
3. 支持购物车过期和清理
4. 包含价格快照和计算逻辑
5. 支持购物车合并和同步
6. 集成库存检查和价格更新

本文件是模型层，定义了数据库表结构和关系。
被数据访问层(CartService)使用来操作数据库。
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, 
    ForeignKey, Enum, JSON, Index, Numeric
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum
import uuid

# 引入数据库基类
from ..core.database import Base


class CartStatus(str, enum.Enum):
    """购物车状态枚举"""
    ACTIVE = "active"        # 活跃
    ABANDONED = "abandoned"  # 废弃
    CONVERTED = "converted"  # 已转换


class Cart(Base):
    """购物车模型"""
    
    __tablename__ = "carts"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 关联用户
    # 这实现了一对多关系：一个用户可以有多个购物车。
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID"
    )
    
    # 购物车状态
    status: Mapped[CartStatus] = mapped_column(
        Enum(CartStatus),
        default=CartStatus.ACTIVE,
        comment="购物车状态"
    )
    
    # 价格信息
    subtotal: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.0,
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
        default=0.0,
        comment="购物车总额"
    )
    
    # 商品统计
    item_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="商品种类数"
    )
    total_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="商品总数量"
    )
    
    # 扩展信息
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="购物车元数据"
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
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(days=30),
        comment="过期时间"
    )
    
    # 关系
    user: Mapped["User"] = relationship(
        "User"
    )
    items: Mapped[List["CartItem"]] = relationship(
        "CartItem", 
        back_populates="cart",
        cascade="all, delete-orphan"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_carts_user", "user_id"),
        Index("idx_carts_status", "status"),
        Index("idx_carts_expires", "expires_at"),
        Index("idx_carts_updated", "updated_at"),
    )
    
    @property
    def is_expired(self) -> bool:
        """购物车是否已过期"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_empty(self) -> bool:
        """购物车是否为空"""
        return self.item_count == 0
    
    def __repr__(self) -> str:
        return f"<Cart(id={self.id}, user_id={self.user_id}, item_count={self.item_count})>"


class CartItem(Base):
    """购物车项模型"""
    
    __tablename__ = "cart_items"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 关联购物车
    cart_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=False,
        comment="购物车ID"
    )
    
    # 关联商品
    product_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("products.id", ondelete="CASCADE"),
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
    
    # 扩展信息
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="购物车项元数据"
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
    cart: Mapped["Cart"] = relationship(
        "Cart", 
        back_populates="items"
    )
    product: Mapped["Product"] = relationship(
        "Product", 
        back_populates="cart_items"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_cart_items_cart", "cart_id"),
        Index("idx_cart_items_product", "product_id"),
        Index("idx_cart_items_cart_product", "cart_id", "product_id", unique=True),
    )
    
    def __repr__(self) -> str:
        return f"<CartItem(id={self.id}, product_name='{self.product_name}', quantity={self.quantity})>"
