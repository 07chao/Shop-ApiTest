"""
用户路由
========
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_async_db
from ...core.security import get_current_active_user, require_admin
from ...services.user_service import UserService
from ...schemas.user import UserUpdate, UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def me(user=Depends(get_current_active_user)):
    return user


@router.patch("/me", response_model=UserResponse)
async def update_me(payload: UserUpdate, db: AsyncSession = Depends(get_async_db), user=Depends(get_current_active_user)):
    svc = UserService(db)
    updated = await svc.update_user(user.id, payload)
    return updated


@router.get("/", dependencies=[Depends(require_admin)])
async def list_users(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_async_db)):
    svc = UserService(db)
    items = await svc.get_users(skip=skip, limit=limit)
    return {"items": items, "total": len(items)}



