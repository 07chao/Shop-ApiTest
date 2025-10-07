"""
AI 嵌入模型
===========

定义 AI 相关的数据模型，包含商品嵌入、向量检索等。
支持向量数据库集成、嵌入生成、相似度计算等功能。

设计思路:
1. 商品嵌入表存储商品的向量表示
2. 支持多种嵌入模型和版本管理
3. 包含嵌入生成状态和元数据
4. 支持嵌入更新和增量同步
5. 包含相似度计算和检索优化
6. 支持嵌入缓存和性能优化
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, 
    ForeignKey, Enum, JSON, Index, Numeric, BigInteger
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import enum
import uuid

from ..core.database import Base


class EmbeddingStatus(str, enum.Enum):
    """嵌入状态枚举"""
    PENDING = "pending"        # 待生成
    PROCESSING = "processing"  # 生成中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 生成失败
    OUTDATED = "outdated"      # 已过期


class EmbeddingModel(str, enum.Enum):
    """嵌入模型枚举"""
    OPENAI_ADA_002 = "text-embedding-ada-002"
    OPENAI_3_SMALL = "text-embedding-3-small"
    OPENAI_3_LARGE = "text-embedding-3-large"
    SENTENCE_TRANSFORMERS = "sentence-transformers"
    LOCAL_MODEL = "local-model"


class ProductEmbedding(Base):
    """商品嵌入模型"""
    
    __tablename__ = "product_embeddings"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 关联商品
    product_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="商品ID"
    )
    
    # 嵌入信息
    embedding_model: Mapped[EmbeddingModel] = mapped_column(
        Enum(EmbeddingModel),
        nullable=False,
        comment="嵌入模型"
    )
    embedding_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="嵌入版本"
    )
    embedding_dimension: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="嵌入维度"
    )
    
    # 嵌入状态
    status: Mapped[EmbeddingStatus] = mapped_column(
        Enum(EmbeddingStatus),
        default=EmbeddingStatus.PENDING,
        comment="嵌入状态"
    )
    
    # 向量数据
    vector_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="向量数据库ID"
    )
    vector_data: Mapped[Optional[List[float]]] = mapped_column(
        ARRAY(Numeric),
        comment="向量数据"
    )
    
    # 源文本信息
    source_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="源文本"
    )
    text_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="文本哈希"
    )
    
    # 生成信息
    generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="生成时间"
    )
    generation_time: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 3),
        comment="生成耗时(秒)"
    )
    
    # 错误信息
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="错误信息"
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="重试次数"
    )
    
    # 扩展信息
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="嵌入元数据"
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
    product: Mapped["Product"] = relationship(
        "Product", 
        back_populates="embedding"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_product_embeddings_product", "product_id"),
        Index("idx_product_embeddings_model", "embedding_model"),
        Index("idx_product_embeddings_status", "status"),
        Index("idx_product_embeddings_vector_id", "vector_id"),
        Index("idx_product_embeddings_text_hash", "text_hash"),
        Index("idx_product_embeddings_created", "created_at"),
    )
    
    @property
    def is_completed(self) -> bool:
        """嵌入是否已完成"""
        return self.status == EmbeddingStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """嵌入是否失败"""
        return self.status == EmbeddingStatus.FAILED
    
    @property
    def needs_update(self) -> bool:
        """是否需要更新"""
        return self.status in [
            EmbeddingStatus.PENDING,
            EmbeddingStatus.FAILED,
            EmbeddingStatus.OUTDATED
        ]
    
    def __repr__(self) -> str:
        return f"<ProductEmbedding(id={self.id}, product_id={self.product_id}, model='{self.embedding_model}', status='{self.status}')>"


class EmbeddingJob(Base):
    """嵌入生成任务模型"""
    
    __tablename__ = "embedding_jobs"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 任务信息
    job_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        comment="任务ID"
    )
    
    # 任务类型
    job_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="任务类型"
    )
    
    # 关联对象
    target_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="目标对象ID"
    )
    target_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="目标对象类型"
    )
    
    # 任务状态
    status: Mapped[EmbeddingStatus] = mapped_column(
        Enum(EmbeddingStatus),
        default=EmbeddingStatus.PENDING,
        comment="任务状态"
    )
    
    # 任务参数
    parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="任务参数"
    )
    
    # 执行信息
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="开始时间"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="完成时间"
    )
    execution_time: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 3),
        comment="执行耗时(秒)"
    )
    
    # 结果信息
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="任务结果"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="错误信息"
    )
    
    # 重试信息
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="重试次数"
    )
    max_retries: Mapped[int] = mapped_column(
        Integer,
        default=3,
        comment="最大重试次数"
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
        Index("idx_embedding_jobs_job_id", "job_id"),
        Index("idx_embedding_jobs_type", "job_type"),
        Index("idx_embedding_jobs_status", "status"),
        Index("idx_embedding_jobs_target", "target_type", "target_id"),
        Index("idx_embedding_jobs_created", "created_at"),
    )
    
    @property
    def is_completed(self) -> bool:
        """任务是否已完成"""
        return self.status == EmbeddingStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """任务是否失败"""
        return self.status == EmbeddingStatus.FAILED
    
    @property
    def can_retry(self) -> bool:
        """是否可以重试"""
        return (
            self.status == EmbeddingStatus.FAILED and
            self.retry_count < self.max_retries
        )
    
    def __repr__(self) -> str:
        return f"<EmbeddingJob(id={self.id}, job_id='{self.job_id}', type='{self.job_type}', status='{self.status}')>"

