"""
AI 助手路由（RAG 占位）
=====================
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_async_db
from ...core.security import require_user, require_merchant
from ...services.ai_service import AIService

router = APIRouter()


@router.post("/embed/{product_id}")
async def generate_embedding(product_id: int, db: AsyncSession = Depends(get_async_db), user=Depends(require_merchant)):
    svc = AIService(db)
    await svc.generate_product_embedding(product_id)
    return {"ok": True}


@router.post("/search")
async def rag_search(query: dict, db: AsyncSession = Depends(get_async_db), user=Depends(require_user)):
    # 占位：返回空候选
    return {"candidates": [], "explanation": "暂未实现，接入向量库后生效"}



