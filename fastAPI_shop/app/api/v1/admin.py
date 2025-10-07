"""
管理员路由（占位）
================
"""
from fastapi import APIRouter, Depends
from ...core.security import require_admin

router = APIRouter()


@router.get("/stats", dependencies=[Depends(require_admin)])
async def platform_stats():
    return {"users": 0, "orders": 0, "products": 0}


