"""
商品路由
========
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_async_db
from ...core.security import require_merchant
from ...services.product_service import ProductService

router = APIRouter()


@router.get("/")
async def list_products(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_async_db)):
    svc = ProductService(db)
    items = await svc.list(skip=skip, limit=limit)
    return {"items": items, "total": len(items)}


@router.post("/", dependencies=[Depends(require_merchant)])
async def create_product(payload: dict, db: AsyncSession = Depends(get_async_db)):
    svc = ProductService(db)
    obj = await svc.create(payload)
    return obj


@router.patch("/{pid}")
async def update_product(pid: int, payload: dict, db: AsyncSession = Depends(get_async_db), user=Depends(require_merchant)):
    svc = ProductService(db)
    obj = await svc.update(pid, payload)
    return obj


@router.post("/{pid}/publish")
async def publish_product(pid: int, active: bool = True, db: AsyncSession = Depends(get_async_db), user=Depends(require_merchant)):
    svc = ProductService(db)
    obj = await svc.publish(pid, active)
    return obj



