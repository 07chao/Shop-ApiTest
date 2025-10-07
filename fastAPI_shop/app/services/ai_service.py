"""
AI 服务
======

封装嵌入生成与简单检索占位。
"""
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.ai_embedding import ProductEmbedding, EmbeddingStatus, EmbeddingModel
from sqlalchemy import select
from datetime import datetime


class AIService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_product_embedding(self, product_id: int) -> None:
        # 简化：仅写入占位记录（生产应调用模型/向量DB）
        res = await self.db.execute(select(ProductEmbedding).where(ProductEmbedding.product_id == product_id))
        emb = res.scalar_one_or_none()
        if emb is None:
            emb = ProductEmbedding(
                product_id=product_id,
                embedding_model=EmbeddingModel.SENTENCE_TRANSFORMERS,
                embedding_version="v1",
                embedding_dimension=384,
                status=EmbeddingStatus.COMPLETED,
                source_text=f"product:{product_id}",
                text_hash=str(product_id),
                generated_at=datetime.utcnow(),
            )
            self.db.add(emb)
        else:
            emb.status = EmbeddingStatus.COMPLETED
            emb.generated_at = datetime.utcnow()
        await self.db.commit()

    async def refresh_outdated_embeddings(self) -> int:
        # 占位：返回0表示无操作
        return 0



