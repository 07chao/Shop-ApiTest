"""
评价路由（占位）
==============
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_async_db
from ...core.security import require_user

router = APIRouter()


@router.get("/")
async def list_reviews(db: AsyncSession = Depends(get_async_db)):
    return {"items": [], "total": 0}


