"""
地址模型
========

定义用户地址相关的数据模型，包含收货地址、配送地址等。
支持地址管理、地址验证、配送范围计算等功能。

设计思路:
1. 地址表存储用户地址信息
2. 支持多种地址类型（家庭、工作、其他）
3. 包含详细的地理位置信息
4. 支持地址验证和标准化
5. 包含配送相关属性
6. 支持地址标签和备注
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


class AddressType(str, enum.Enum):
    """地址类型枚举"""
    HOME = "home"          # 家庭地址
    WORK = "work"          # 工作地址
    OTHER = "other"        # 其他地址


class Address(Base):
    """地址模型"""
    
    __tablename__ = "addresses"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 关联用户
    user_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID"
    )
    
    # 地址类型
    address_type: Mapped[AddressType] = mapped_column(
        Enum(AddressType),
        default=AddressType.HOME,
        comment="地址类型"
    )
    
    # 联系人信息
    contact_name: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="联系人姓名"
    )
    contact_phone: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        comment="联系电话"
    )
    
    # 地址信息
    country: Mapped[str] = mapped_column(
        String(50), 
        default="中国",
        comment="国家"
    )
    province: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="省份"
    )
    city: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="城市"
    )
    district: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="区县"
    )
    street: Mapped[str] = mapped_column(
        String(200), 
        nullable=False,
        comment="街道"
    )
    address_detail: Mapped[str] = mapped_column(
        String(500), 
        nullable=False,
        comment="详细地址"
    )
    postal_code: Mapped[Optional[str]] = mapped_column(
        String(10),
        comment="邮政编码"
    )
    
    # 地理位置信息
    latitude: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 8),
        comment="纬度"
    )
    longitude: Mapped[Optional[float]] = mapped_column(
        Numeric(11, 8),
        comment="经度"
    )
    
    # 地址标签
    label: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="地址标签"
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否默认地址"
    )
    
    # 配送信息
    delivery_instructions: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="配送说明"
    )
    access_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        comment="门禁密码"
    )
    building: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="楼栋"
    )
    floor: Mapped[Optional[str]] = mapped_column(
        String(20),
        comment="楼层"
    )
    room: Mapped[Optional[str]] = mapped_column(
        String(20),
        comment="房间号"
    )
    
    # 状态信息
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否激活"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否已验证"
    )
    
    # 扩展信息
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="地址元数据"
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
        back_populates="addresses"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_addresses_user", "user_id"),
        Index("idx_addresses_type", "address_type"),
        Index("idx_addresses_city", "city"),
        Index("idx_addresses_coordinates", "latitude", "longitude"),
        Index("idx_addresses_default", "user_id", "is_default"),
    )
    
    @property
    def full_address(self) -> str:
        """获取完整地址"""
        parts = [
            self.country,
            self.province,
            self.city,
            self.district,
            self.street,
            self.address_detail
        ]
        return "".join(filter(None, parts))
    
    @property
    def short_address(self) -> str:
        """获取简短地址"""
        parts = [
            self.city,
            self.district,
            self.street
        ]
        return "".join(filter(None, parts))
    
    def __repr__(self) -> str:
        return f"<Address(id={self.id}, user_id={self.user_id}, address_type='{self.address_type}')>"

