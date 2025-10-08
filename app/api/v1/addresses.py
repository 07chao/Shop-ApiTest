"""
地址路由（占位）
==============
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_async_db
from ...core.security import require_user

router = APIRouter()


@router.get("/")
async def list_addresses(db: AsyncSession = Depends(get_async_db), user=Depends(require_user)):
    # 占位：返回空列表，后续可接入 AddressService
    return {"items": [], "total": 0}


