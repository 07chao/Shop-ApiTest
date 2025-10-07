"""
通知路由（占位）
==============
"""
from fastapi import APIRouter, Depends
from ...core.security import require_user

router = APIRouter()


@router.get("/")
async def list_notifications(user=Depends(require_user)):
    return {"items": [], "total": 0}


