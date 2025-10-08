"""
商家服务
========
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.user import Merchant


class MerchantService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user(self, user_id: int) -> Merchant | None:
        res = await self.db.execute(select(Merchant).where(Merchant.user_id == user_id))
        return res.scalar_one_or_none()



