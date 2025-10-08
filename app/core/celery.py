"""
Celery 初始化
===========

提供 Celery 应用、队列与定时任务（Beat）初始化。
生产中可切换为 RabbitMQ/Kafka 作为 broker；示例默认使用 Redis。
"""

from celery import Celery
from celery.schedules import crontab
import os

from .config import settings


def _broker_url() -> str:
    return os.getenv("CELERY_BROKER_URL", settings.celery_broker_url)


def _result_backend() -> str:
    return os.getenv("CELERY_RESULT_BACKEND", settings.celery_result_backend)


celery_app = Celery(
    "fastapi_shop",
    broker=_broker_url(),
    backend=_result_backend(),
    include=[
        "app.tasks.ai_tasks",
        "app.tasks.email_tasks",
        "app.tasks.inventory_tasks",
    ],
)

# 基础配置（可按需扩展）
celery_app.conf.update(
    timezone="Asia/Shanghai",
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    task_default_queue="default",
    beat_schedule={
        # 示例：每小时同步商品 embedding 过期项
        "sync-outdated-embeddings": {
            "task": "app.tasks.ai_tasks.refresh_outdated_embeddings",
            "schedule": crontab(minute=0, hour="*"),
        },
    },
)


@celery_app.task(name="app.tasks.heartbeat")
def heartbeat() -> str:
    """心跳任务：用于健康检查与演示"""
    return "ok"



