"""
支付路由（模拟）
==============
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...core.database import get_async_db
from ...core.security import require_user
from ...services.payment_service import PaymentService
from ...models.order import Order

router = APIRouter()


@router.post("/intent/{order_id}")
async def create_intent(order_id: int, db: AsyncSession = Depends(get_async_db), user=Depends(require_user)):
    order = (await db.execute(select(Order).where(Order.id == order_id))).scalar_one_or_none()
    if not order or order.user_id != user.id:
        raise HTTPException(status_code=404, detail="订单不存在")
    svc = PaymentService(db)
    pay = await svc.create_payment_intent(order)
    return pay


@router.post("/callback/{order_id}")
async def mock_callback(order_id: int, db: AsyncSession = Depends(get_async_db)):
    order = (await db.execute(select(Order).where(Order.id == order_id))).scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    svc = PaymentService(db)
    await svc.mark_paid(order)
    return {"ok": True}



