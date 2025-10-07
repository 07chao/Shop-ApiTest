"""
邮件相关任务
===========
"""
from ..core.celery import celery_app
from ..services.email_service import EmailService


@celery_app.task(name="app.tasks.email_tasks.send_email")
def send_email(to_email: str, subject: str, html_content: str, text_content: str | None = None) -> bool:
    svc = EmailService()
    # 简化：同步调用（生产建议异步SMTP或事务外发）
    return svc.send_email(to_email, subject, html_content, text_content)  # type: ignore



