"""
商家路由
========
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_async_db
from ...core.security import require_merchant
from ...services.merchant_service import MerchantService

router = APIRouter()


@router.get("/me")
async def my_merchant(db: AsyncSession = Depends(get_async_db), user=Depends(require_merchant)):
    svc = MerchantService(db)
    m = await svc.get_by_user(user.id)
    if not m:
        raise HTTPException(status_code=404, detail="未找到商家档案")
    return m



