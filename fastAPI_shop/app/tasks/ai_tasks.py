"""
AI 相关异步任务
==============

用于生成/刷新商品嵌入、调用向量库、异步文案等。
"""

from ..core.celery import celery_app
from ..services.ai_service import AIService
from ..core.database import AsyncSessionLocal
import asyncio


@celery_app.task(name="app.tasks.ai_tasks.generate_product_embedding", acks_late=True)
def generate_product_embedding(product_id: int) -> str:
    """生成商品的向量嵌入（同步包装异步）。"""
    async def _run():
        async with AsyncSessionLocal() as db:
            svc = AIService(db)
            await svc.generate_product_embedding(product_id)
    asyncio.run(_run())
    return "ok"


@celery_app.task(name="app.tasks.ai_tasks.refresh_outdated_embeddings", acks_late=True)
def refresh_outdated_embeddings() -> str:
    async def _run():
        async with AsyncSessionLocal() as db:
            svc = AIService(db)
            await svc.refresh_outdated_embeddings()
    asyncio.run(_run())
    return "ok"



