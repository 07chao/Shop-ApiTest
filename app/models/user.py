"""
用户和商家模型
==============

定义用户、商家等核心用户模型，包含认证、权限、个人信息等功能。

设计思路:
1. 用户表存储基础认证信息
2. 商家表扩展用户信息，支持多租户
3. 使用角色基础的权限控制
4. 支持用户状态管理（激活、禁用等）
5. 包含审计字段（创建时间、更新时间）
6. 支持软删除
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, 
    ForeignKey, Enum, JSON, Index
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum
import uuid

from ..core.database import Base


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    USER = "user"          # 普通用户
    MERCHANT = "merchant"  # 商家
    ADMIN = "admin"        # 管理员


class UserStatus(str, enum.Enum):
    """用户状态枚举"""
    PENDING = "pending"    # 待激活
    ACTIVE = "active"      # 激活
    SUSPENDED = "suspended"  # 暂停
    BANNED = "banned"      # 封禁


class User(Base):
    """用户模型"""
    
    __tablename__ = "users"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 基础信息
    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        index=True, 
        nullable=False,
        comment="用户邮箱"
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(50), 
        unique=True, 
        index=True,
        comment="用户名"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20), 
        unique=True, 
        index=True,
        comment="手机号"
    )
    
    # 认证信息
    password_hash: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        comment="密码哈希"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True,
        comment="是否激活"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        comment="是否已验证邮箱"
    )
    
    # 角色和权限
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.USER,
        comment="用户角色"
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus),
        default=UserStatus.PENDING,
        comment="用户状态"
    )
    
    # 个人信息
    first_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="名"
    )
    last_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="姓"
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="头像URL"
    )
    bio: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="个人简介"
    )
    
    # 扩展信息 (JSONB 存储灵活数据)
    profile_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        comment="扩展个人信息"
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
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="最后登录时间"
    )
    
    # 软删除
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        comment="是否已删除"
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="删除时间"
    )
    
    # 关系
    merchant: Mapped[Optional["Merchant"]] = relationship(
        "Merchant", 
        back_populates="user", 
        uselist=False
    )
    addresses: Mapped[List["Address"]] = relationship(
        "Address", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    orders: Mapped[List["Order"]] = relationship(
        "Order", 
        back_populates="user"
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review", 
        back_populates="user"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", 
        back_populates="user"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_users_email_active", "email", "is_active"),
        Index("idx_users_role_status", "role", "status"),
        Index("idx_users_created_at", "created_at"),
    )
    
    @property
    def full_name(self) -> str:
        """获取全名"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username or self.email.split("@")[0]
    
    @property
    def is_merchant(self) -> bool:
        """是否为商家"""
        return self.role in [UserRole.MERCHANT, UserRole.ADMIN]
    
    @property
    def is_admin(self) -> bool:
        """是否为管理员"""
        return self.role == UserRole.ADMIN
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class Merchant(Base):
    """商家模型"""
    
    __tablename__ = "merchants"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 关联用户
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        comment="关联用户ID"
    )
    
    # 商家信息
    business_name: Mapped[str] = mapped_column(
        String(200), 
        nullable=False,
        comment="商家名称"
    )
    business_license: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="营业执照号"
    )
    business_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="商家类型"
    )
    
    # 联系信息
    contact_person: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="联系人"
    )
    contact_phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        comment="联系电话"
    )
    contact_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="联系邮箱"
    )
    
    # 地址信息
    business_address: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="商家地址"
    )
    business_city: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="所在城市"
    )
    business_province: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="所在省份"
    )
    
    # 商家状态
    is_verified: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        comment="是否已认证"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True,
        comment="是否激活"
    )
    
    # 商家设置
    delivery_radius: Mapped[Optional[int]] = mapped_column(
        Integer,
        default=5,
        comment="配送半径(公里)"
    )
    delivery_fee: Mapped[Optional[float]] = mapped_column(
        default=0.0,
        comment="配送费"
    )
    min_order_amount: Mapped[Optional[float]] = mapped_column(
        default=0.0,
        comment="最低起送金额"
    )
    
    # 扩展信息
    business_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        comment="商家扩展信息"
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
        back_populates="merchant"
    )
    products: Mapped[List["Product"]] = relationship(
        "Product", 
        back_populates="merchant",
        cascade="all, delete-orphan"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_merchants_user_id", "user_id"),
        Index("idx_merchants_business_name", "business_name"),
        Index("idx_merchants_city", "business_city"),
        Index("idx_merchants_active", "is_active"),
    )
    
    @property
    def display_name(self) -> str:
        """获取显示名称"""
        return self.business_name or self.user.full_name
    
    def __repr__(self) -> str:
        return f"<Merchant(id={self.id}, business_name='{self.business_name}')>"

