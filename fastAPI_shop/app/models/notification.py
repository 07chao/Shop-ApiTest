"""
通知模型
========

定义用户通知相关的数据模型，包含系统通知、消息推送等。
支持通知管理、消息分类、推送状态跟踪等功能。

设计思路:
1. 通知表存储用户通知信息
2. 支持多种通知类型和优先级
3. 包含通知状态管理（未读、已读、已删除）
4. 支持通知模板和个性化内容
5. 包含推送状态跟踪
6. 支持通知统计和分析
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


class NotificationType(str, enum.Enum):
    """通知类型枚举"""
    SYSTEM = "system"          # 系统通知
    ORDER = "order"            # 订单通知
    PAYMENT = "payment"        # 支付通知
    DELIVERY = "delivery"      # 配送通知
    PROMOTION = "promotion"    # 促销通知
    REVIEW = "review"          # 评价通知
    ACCOUNT = "account"        # 账户通知


class NotificationPriority(str, enum.Enum):
    """通知优先级枚举"""
    LOW = "low"                # 低优先级
    NORMAL = "normal"          # 普通优先级
    HIGH = "high"              # 高优先级
    URGENT = "urgent"          # 紧急优先级


class NotificationStatus(str, enum.Enum):
    """通知状态枚举"""
    UNREAD = "unread"          # 未读
    READ = "read"              # 已读
    DELETED = "deleted"        # 已删除


class Notification(Base):
    """通知模型"""
    
    __tablename__ = "notifications"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 关联用户
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID"
    )
    
    # 通知类型
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType),
        nullable=False,
        comment="通知类型"
    )
    
    # 优先级
    priority: Mapped[NotificationPriority] = mapped_column(
        Enum(NotificationPriority),
        default=NotificationPriority.NORMAL,
        comment="通知优先级"
    )
    
    # 通知内容
    title: Mapped[str] = mapped_column(
        String(200), 
        nullable=False,
        comment="通知标题"
    )
    content: Mapped[str] = mapped_column(
        Text, 
        nullable=False,
        comment="通知内容"
    )
    summary: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="通知摘要"
    )
    
    # 通知状态
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus),
        default=NotificationStatus.UNREAD,
        comment="通知状态"
    )
    
    # 关联信息
    related_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="关联对象ID"
    )
    related_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="关联对象类型"
    )
    
    # 推送信息
    push_sent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否已推送"
    )
    push_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="推送时间"
    )
    push_failed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="推送是否失败"
    )
    push_error: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="推送错误信息"
    )
    
    # 阅读信息
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="阅读时间"
    )
    
    # 操作信息
    action_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="操作链接"
    )
    action_text: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="操作按钮文本"
    )
    
    # 扩展信息
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="通知元数据"
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
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="过期时间"
    )
    
    # 关系
    user: Mapped["User"] = relationship(
        "User", 
        back_populates="notifications"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_notifications_user", "user_id"),
        Index("idx_notifications_type", "notification_type"),
        Index("idx_notifications_status", "status"),
        Index("idx_notifications_priority", "priority"),
        Index("idx_notifications_created", "created_at"),
        Index("idx_notifications_user_status", "user_id", "status"),
        Index("idx_notifications_user_type", "user_id", "notification_type"),
    )
    
    @property
    def is_unread(self) -> bool:
        """是否未读"""
        return self.status == NotificationStatus.UNREAD
    
    @property
    def is_expired(self) -> bool:
        """是否已过期"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def mark_as_read(self) -> None:
        """标记为已读"""
        self.status = NotificationStatus.READ
        self.read_at = datetime.utcnow()
    
    def mark_as_deleted(self) -> None:
        """标记为已删除"""
        self.status = NotificationStatus.DELETED
    
    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, user_id={self.user_id}, type='{self.notification_type}', status='{self.status}')>"

