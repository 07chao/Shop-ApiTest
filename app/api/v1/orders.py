"""
订单路由
=======
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_async_db
from ...core.security import require_user
from ...services.order_service import OrderService

router = APIRouter()


@router.post("/")
async def create_order(items: list[dict], db: AsyncSession = Depends(get_async_db), user=Depends(require_user)):
    svc = OrderService(db)
    order = await svc.create_simple(user.id, items)
    return order



