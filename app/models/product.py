"""
商品模型
========

定义商品相关的数据模型，包含商品信息、分类、标签、图片等。
支持多规格商品、库存管理、价格策略等功能。

设计思路:
1. 商品表存储基础商品信息
2. 商品图片表支持多图片
3. 商品分类和标签支持层级结构
4. 使用 JSONB 存储商品规格和属性
5. 支持商品状态管理（草稿、上架、下架等）
6. 包含销量统计和评分信息
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, 
    ForeignKey, Enum, JSON, Index, Numeric, BigInteger
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import enum
import uuid

from ..core.database import Base


class ProductStatus(str, enum.Enum):
    """商品状态枚举"""
    DRAFT = "draft"        # 草稿
    PENDING = "pending"    # 待审核
    ACTIVE = "active"      # 上架
    INACTIVE = "inactive"  # 下架
    OUT_OF_STOCK = "out_of_stock"  # 缺货


class ProductType(str, enum.Enum):
    """商品类型枚举"""
    PHYSICAL = "physical"  # 实物商品
    DIGITAL = "digital"    # 数字商品
    SERVICE = "service"    # 服务


class Product(Base):
    """商品模型"""
    
    __tablename__ = "products"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 关联商家
    merchant_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        comment="商家ID"
    )
    
    # 基础信息
    title: Mapped[str] = mapped_column(
        String(200), 
        nullable=False,
        comment="商品标题"
    )
    subtitle: Mapped[Optional[str]] = mapped_column(
        String(300),
        comment="商品副标题"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="商品描述"
    )
    short_description: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="商品简介"
    )
    
    # 商品类型和状态
    product_type: Mapped[ProductType] = mapped_column(
        Enum(ProductType),
        default=ProductType.PHYSICAL,
        comment="商品类型"
    )
    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus),
        default=ProductStatus.DRAFT,
        comment="商品状态"
    )
    
    # 价格信息
    price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="商品价格"
    )
    original_price: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2),
        comment="原价"
    )
    cost_price: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2),
        comment="成本价"
    )
    
    # 库存信息
    stock: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="库存数量"
    )
    min_stock: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="最低库存"
    )
    max_stock: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="最大库存"
    )
    
    # 分类和标签
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("product_categories.id"),
        comment="商品分类ID"
    )
    tags: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        comment="商品标签"
    )
    
    # 商品属性 (JSONB 存储灵活数据)
    attributes: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="商品属性"
    )
    specifications: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="商品规格"
    )
    variants: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB,
        comment="商品变体"
    )
    
    # 统计信息
    view_count: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        comment="浏览次数"
    )
    sales_count: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        comment="销售数量"
    )
    favorite_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="收藏数量"
    )
    
    # 评分信息
    rating: Mapped[Optional[float]] = mapped_column(
        default=0.0,
        comment="平均评分"
    )
    review_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="评价数量"
    )
    
    # SEO 信息
    slug: Mapped[Optional[str]] = mapped_column(
        String(200),
        unique=True,
        index=True,
        comment="URL 别名"
    )
    meta_title: Mapped[Optional[str]] = mapped_column(
        String(200),
        comment="SEO 标题"
    )
    meta_description: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="SEO 描述"
    )
    meta_keywords: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="SEO 关键词"
    )
    
    # 配送信息
    weight: Mapped[Optional[float]] = mapped_column(
        default=0.0,
        comment="重量(kg)"
    )
    dimensions: Mapped[Optional[Dict[str, float]]] = mapped_column(
        JSONB,
        comment="尺寸信息"
    )
    shipping_class: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="配送类别"
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
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="发布时间"
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
    merchant: Mapped["Merchant"] = relationship(
        "Merchant", 
        back_populates="products"
    )
    category: Mapped[Optional["ProductCategory"]] = relationship(
        "ProductCategory", 
        back_populates="products"
    )
    images: Mapped[List["ProductImage"]] = relationship(
        "ProductImage", 
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductImage.order_index"
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review", 
        back_populates="product"
    )
    order_items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", 
        back_populates="product"
    )
    cart_items: Mapped[List["CartItem"]] = relationship(
        "CartItem", 
        back_populates="product"
    )
    embedding: Mapped[Optional["ProductEmbedding"]] = relationship(
        "ProductEmbedding", 
        back_populates="product",
        uselist=False
    )
    
    # 索引
    __table_args__ = (
        Index("idx_products_merchant_status", "merchant_id", "status"),
        Index("idx_products_category", "category_id"),
        Index("idx_products_price", "price"),
        Index("idx_products_rating", "rating"),
        Index("idx_products_sales", "sales_count"),
        Index("idx_products_created", "created_at"),
        Index("idx_products_published", "published_at"),
        Index("idx_products_tags", "tags", postgresql_using="gin"),
        Index("idx_products_attributes", "attributes", postgresql_using="gin"),
    )
    
    @property
    def is_available(self) -> bool:
        """商品是否可用"""
        return (
            self.status == ProductStatus.ACTIVE and 
            self.stock > 0 and 
            not self.is_deleted
        )
    
    @property
    def discount_percentage(self) -> Optional[float]:
        """折扣百分比"""
        if self.original_price and self.original_price > self.price:
            return round((1 - self.price / self.original_price) * 100, 2)
        return None
    
    @property
    def main_image(self) -> Optional["ProductImage"]:
        """主图片"""
        if self.images:
            return self.images[0]
        return None
    
    def __repr__(self) -> str:
        return f"<Product(id={self.id}, title='{self.title}', price={self.price})>"


class ProductImage(Base):
    """商品图片模型"""
    
    __tablename__ = "product_images"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 关联商品
    product_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        comment="商品ID"
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
    title: Mapped[Optional[str]] = mapped_column(
        String(200),
        comment="图片标题"
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
    
    # 排序和状态
    order_index: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="排序索引"
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否为主图"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否激活"
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,
        comment="创建时间"
    )
    
    # 关系
    product: Mapped["Product"] = relationship(
        "Product", 
        back_populates="images"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_product_images_product", "product_id"),
        Index("idx_product_images_order", "product_id", "order_index"),
    )
    
    def __repr__(self) -> str:
        return f"<ProductImage(id={self.id}, product_id={self.product_id}, url='{self.url}')>"


class ProductCategory(Base):
    """商品分类模型"""
    
    __tablename__ = "product_categories"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 分类信息
    name: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="分类名称"
    )
    slug: Mapped[str] = mapped_column(
        String(100), 
        unique=True,
        index=True,
        comment="URL 别名"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="分类描述"
    )
    
    # 层级结构
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("product_categories.id"),
        comment="父分类ID"
    )
    level: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="分类层级"
    )
    path: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="分类路径"
    )
    
    # 排序和状态
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="排序"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否激活"
    )
    
    # 图标和图片
    icon: Mapped[Optional[str]] = mapped_column(
        String(200),
        comment="分类图标"
    )
    image_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="分类图片"
    )
    
    # SEO 信息
    meta_title: Mapped[Optional[str]] = mapped_column(
        String(200),
        comment="SEO 标题"
    )
    meta_description: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="SEO 描述"
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
    parent: Mapped[Optional["ProductCategory"]] = relationship(
        "ProductCategory", 
        remote_side=[id],
        back_populates="children"
    )
    children: Mapped[List["ProductCategory"]] = relationship(
        "ProductCategory", 
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    products: Mapped[List["Product"]] = relationship(
        "Product", 
        back_populates="category"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_product_categories_parent", "parent_id"),
        Index("idx_product_categories_level", "level"),
        Index("idx_product_categories_active", "is_active"),
    )
    
    @property
    def full_path(self) -> str:
        """获取完整路径"""
        if self.path:
            return self.path
        return self.name
    
    def __repr__(self) -> str:
        return f"<ProductCategory(id={self.id}, name='{self.name}', level={self.level})>"


class ProductTag(Base):
    """商品标签模型"""
    
    __tablename__ = "product_tags"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 标签信息
    name: Mapped[str] = mapped_column(
        String(50), 
        unique=True,
        nullable=False,
        comment="标签名称"
    )
    slug: Mapped[str] = mapped_column(
        String(50), 
        unique=True,
        index=True,
        comment="URL 别名"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(200),
        comment="标签描述"
    )
    color: Mapped[Optional[str]] = mapped_column(
        String(7),
        comment="标签颜色"
    )
    
    # 统计信息
    usage_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="使用次数"
    )
    
    # 状态
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否激活"
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
        Index("idx_product_tags_name", "name"),
        Index("idx_product_tags_active", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<ProductTag(id={self.id}, name='{self.name}')>"

