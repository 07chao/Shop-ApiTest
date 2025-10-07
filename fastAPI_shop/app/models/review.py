"""
评价模型
========

定义商品评价相关的数据模型，包含评价、评价图片等。
支持评价管理、评分统计、评价审核等功能。

设计思路:
1. 评价表存储用户对商品的评价
2. 评价图片表支持多图片上传
3. 包含评分、内容、标签等信息
4. 支持评价回复和互动
5. 包含评价状态管理
6. 支持评价统计和分析
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


class ReviewStatus(str, enum.Enum):
    """评价状态枚举"""
    PENDING = "pending"        # 待审核
    APPROVED = "approved"      # 已通过
    REJECTED = "rejected"      # 已拒绝
    HIDDEN = "hidden"          # 已隐藏


class ReviewType(str, enum.Enum):
    """评价类型枚举"""
    PRODUCT = "product"        # 商品评价
    MERCHANT = "merchant"      # 商家评价
    DELIVERY = "delivery"      # 配送评价


class Review(Base):
    """评价模型"""
    
    __tablename__ = "reviews"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 关联用户
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID"
    )
    
    # 关联商品
    product_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        comment="商品ID"
    )
    
    # 关联订单
    order_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("orders.id"),
        comment="订单ID"
    )
    
    # 评价类型
    review_type: Mapped[ReviewType] = mapped_column(
        Enum(ReviewType),
        default=ReviewType.PRODUCT,
        comment="评价类型"
    )
    
    # 评分信息
    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="评分(1-5)"
    )
    quality_rating: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="质量评分"
    )
    service_rating: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="服务评分"
    )
    delivery_rating: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="配送评分"
    )
    
    # 评价内容
    title: Mapped[Optional[str]] = mapped_column(
        String(200),
        comment="评价标题"
    )
    content: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="评价内容"
    )
    
    # 评价标签
    tags: Mapped[Optional[List[str]]] = mapped_column(
        JSONB,
        comment="评价标签"
    )
    
    # 评价状态
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus),
        default=ReviewStatus.PENDING,
        comment="评价状态"
    )
    
    # 审核信息
    reviewed_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        comment="审核人ID"
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="审核时间"
    )
    review_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="审核备注"
    )
    
    # 互动信息
    like_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="点赞数"
    )
    reply_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="回复数"
    )
    
    # 是否匿名
    is_anonymous: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否匿名"
    )
    
    # 扩展信息
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="评价元数据"
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
        back_populates="reviews"
    )
    product: Mapped["Product"] = relationship(
        "Product", 
        back_populates="reviews"
    )
    order: Mapped[Optional["Order"]] = relationship(
        "Order"
    )
    reviewer: Mapped[Optional["User"]] = relationship(
        "User", 
        foreign_keys=[reviewed_by]
    )
    images: Mapped[List["ReviewImage"]] = relationship(
        "ReviewImage", 
        back_populates="review",
        cascade="all, delete-orphan"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_reviews_user", "user_id"),
        Index("idx_reviews_product", "product_id"),
        Index("idx_reviews_order", "order_id"),
        Index("idx_reviews_rating", "rating"),
        Index("idx_reviews_status", "status"),
        Index("idx_reviews_created", "created_at"),
        Index("idx_reviews_product_rating", "product_id", "rating"),
    )
    
    @property
    def is_approved(self) -> bool:
        """评价是否已通过"""
        return self.status == ReviewStatus.APPROVED
    
    @property
    def display_name(self) -> str:
        """获取显示名称"""
        if self.is_anonymous:
            return "匿名用户"
        return self.user.full_name
    
    def __repr__(self) -> str:
        return f"<Review(id={self.id}, user_id={self.user_id}, product_id={self.product_id}, rating={self.rating})>"


class ReviewImage(Base):
    """评价图片模型"""
    
    __tablename__ = "review_images"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 关联评价
    review_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False,
        comment="评价ID"
    )
    
    # 图片信息
    url: Mapped[str] = mapped_column(
        String(500), 
        nullable=False,
        comment="图片URL"
    )
    alt_text: Mapped[Optional[str]] = mapped_column(
        String(200),
        comment="图片描述"
    )
    
    # 图片属性
    width: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="图片宽度"
    )
    height: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="图片高度"
    )
    file_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="文件大小(字节)"
    )
    mime_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="MIME 类型"
    )
    
    # 排序
    order_index: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="排序索引"
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,
        comment="创建时间"
    )
    
    # 关系
    review: Mapped["Review"] = relationship(
        "Review", 
        back_populates="images"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_review_images_review", "review_id"),
        Index("idx_review_images_order", "review_id", "order_index"),
    )
    
    def __repr__(self) -> str:
        return f"<ReviewImage(id={self.id}, review_id={self.review_id}, url='{self.url}')>"

