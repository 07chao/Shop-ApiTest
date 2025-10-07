"""
库存与订单异步任务
==================
"""
from ..core.celery import celery_app


@celery_app.task(name="app.tasks.inventory_tasks.release_stock")
def release_stock(order_id: int) -> str:
    # TODO: 查询订单状态，释放占用库存（演示占位）
    return f"released:{order_id}"



