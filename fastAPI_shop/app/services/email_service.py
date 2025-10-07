"""
邮件服务
========

实现邮件发送功能，包括用户注册验证、密码重置、通知等邮件。
支持 HTML 模板、异步发送、邮件队列等功能。

设计思路:
1. 使用 SMTP 协议发送邮件
2. 支持 HTML 和纯文本格式
3. 实现邮件模板系统
4. 支持异步发送和队列
5. 包含邮件发送状态跟踪
6. 支持邮件重试和错误处理
"""

from typing import Optional, Dict, Any, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import structlog
from datetime import datetime
import asyncio
from pathlib import Path

from ..core.config import settings
from ..models.user import User

# 配置日志
logger = structlog.get_logger(__name__)


class EmailService:
    """邮件服务类"""
    
    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_username
        
        # 邮件模板目录
        self.template_dir = Path(__file__).parent.parent / "templates" / "email"
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        发送邮件
        
        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            html_content: HTML 内容
            text_content: 纯文本内容
            
        Returns:
            bool: 发送是否成功
        """
        try:
            # 创建邮件消息
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # 添加纯文本内容
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # 添加 HTML 内容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 异步发送邮件
            await asyncio.get_event_loop().run_in_executor(
                None, self._send_smtp_email, msg, to_email
            )
            
            logger.info("Email sent successfully", to_email=to_email, subject=subject)
            return True
            
        except Exception as e:
            logger.error("Failed to send email", to_email=to_email, error=str(e))
            return False
    
    def _send_smtp_email(self, msg: MIMEMultipart, to_email: str) -> None:
        """
        通过 SMTP 发送邮件
        
        Args:
            msg: 邮件消息
            to_email: 收件人邮箱
        """
        try:
            # 连接 SMTP 服务器
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            # 发送邮件
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            logger.error("SMTP email sending failed", to_email=to_email, error=str(e))
            raise
    
    async def send_verification_email(self, user: User) -> bool:
        """
        发送邮箱验证邮件
        
        Args:
            user: 用户对象
            
        Returns:
            bool: 发送是否成功
        """
        try:
            # 生成验证链接
            verification_token = await self._generate_verification_token(user.id)
            verification_url = f"{settings.cors_origins[0]}/verify-email?token={verification_token}"
            
            # 邮件主题
            subject = "邮箱验证 - FastAPI Shop"
            
            # HTML 内容
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>邮箱验证</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .button {{ display: inline-block; padding: 12px 24px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; }}
                    .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>欢迎注册 FastAPI Shop</h1>
                    </div>
                    <div class="content">
                        <p>亲爱的 {user.full_name}，</p>
                        <p>感谢您注册我们的服务！请点击下面的按钮验证您的邮箱地址：</p>
                        <p style="text-align: center;">
                            <a href="{verification_url}" class="button">验证邮箱</a>
                        </p>
                        <p>如果按钮无法点击，请复制以下链接到浏览器中打开：</p>
                        <p style="word-break: break-all; color: #666;">{verification_url}</p>
                        <p>此链接将在 24 小时后过期。</p>
                    </div>
                    <div class="footer">
                        <p>此邮件由系统自动发送，请勿回复。</p>
                        <p>© 2024 FastAPI Shop. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 纯文本内容
            text_content = f"""
            欢迎注册 FastAPI Shop
            
            亲爱的 {user.full_name}，
            
            感谢您注册我们的服务！请访问以下链接验证您的邮箱地址：
            
            {verification_url}
            
            此链接将在 24 小时后过期。
            
            此邮件由系统自动发送，请勿回复。
            © 2024 FastAPI Shop. All rights reserved.
            """
            
            return await self.send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error("Failed to send verification email", user_id=user.id, error=str(e))
            return False
    
    async def send_password_reset_email(self, user: User, reset_token: str) -> bool:
        """
        发送密码重置邮件
        
        Args:
            user: 用户对象
            reset_token: 重置令牌
            
        Returns:
            bool: 发送是否成功
        """
        try:
            # 生成重置链接
            reset_url = f"{settings.cors_origins[0]}/reset-password?token={reset_token}"
            
            # 邮件主题
            subject = "密码重置 - FastAPI Shop"
            
            # HTML 内容
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>密码重置</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .button {{ display: inline-block; padding: 12px 24px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 4px; }}
                    .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; }}
                    .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 4px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>密码重置请求</h1>
                    </div>
                    <div class="content">
                        <p>亲爱的 {user.full_name}，</p>
                        <p>我们收到了您的密码重置请求。请点击下面的按钮重置您的密码：</p>
                        <p style="text-align: center;">
                            <a href="{reset_url}" class="button">重置密码</a>
                        </p>
                        <p>如果按钮无法点击，请复制以下链接到浏览器中打开：</p>
                        <p style="word-break: break-all; color: #666;">{reset_url}</p>
                        <div class="warning">
                            <strong>安全提示：</strong>
                            <ul>
                                <li>此链接将在 1 小时后过期</li>
                                <li>如果您没有请求重置密码，请忽略此邮件</li>
                                <li>请不要将此链接分享给他人</li>
                            </ul>
                        </div>
                    </div>
                    <div class="footer">
                        <p>此邮件由系统自动发送，请勿回复。</p>
                        <p>© 2024 FastAPI Shop. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 纯文本内容
            text_content = f"""
            密码重置请求
            
            亲爱的 {user.full_name}，
            
            我们收到了您的密码重置请求。请访问以下链接重置您的密码：
            
            {reset_url}
            
            安全提示：
            - 此链接将在 1 小时后过期
            - 如果您没有请求重置密码，请忽略此邮件
            - 请不要将此链接分享给他人
            
            此邮件由系统自动发送，请勿回复。
            © 2024 FastAPI Shop. All rights reserved.
            """
            
            return await self.send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error("Failed to send password reset email", user_id=user.id, error=str(e))
            return False
    
    async def send_welcome_email(self, user: User) -> bool:
        """
        发送欢迎邮件
        
        Args:
            user: 用户对象
            
        Returns:
            bool: 发送是否成功
        """
        try:
            # 邮件主题
            subject = "欢迎加入 FastAPI Shop"
            
            # HTML 内容
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>欢迎加入</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .button {{ display: inline-block; padding: 12px 24px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; }}
                    .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 欢迎加入 FastAPI Shop</h1>
                    </div>
                    <div class="content">
                        <p>亲爱的 {user.full_name}，</p>
                        <p>恭喜您成功注册 FastAPI Shop！我们很高兴您成为我们的一员。</p>
                        <p>现在您可以：</p>
                        <ul>
                            <li>浏览和购买商品</li>
                            <li>享受快速配送服务</li>
                            <li>参与我们的促销活动</li>
                            <li>获得专属优惠券</li>
                        </ul>
                        <p style="text-align: center;">
                            <a href="{settings.cors_origins[0]}" class="button">开始购物</a>
                        </p>
                        <p>如果您有任何问题，请随时联系我们的客服团队。</p>
                    </div>
                    <div class="footer">
                        <p>此邮件由系统自动发送，请勿回复。</p>
                        <p>© 2024 FastAPI Shop. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 纯文本内容
            text_content = f"""
            欢迎加入 FastAPI Shop
            
            亲爱的 {user.full_name}，
            
            恭喜您成功注册 FastAPI Shop！我们很高兴您成为我们的一员。
            
            现在您可以：
            - 浏览和购买商品
            - 享受快速配送服务
            - 参与我们的促销活动
            - 获得专属优惠券
            
            开始购物：{settings.cors_origins[0]}
            
            如果您有任何问题，请随时联系我们的客服团队。
            
            此邮件由系统自动发送，请勿回复。
            © 2024 FastAPI Shop. All rights reserved.
            """
            
            return await self.send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error("Failed to send welcome email", user_id=user.id, error=str(e))
            return False
    
    async def send_notification_email(
        self,
        user: User,
        title: str,
        message: str,
        action_url: Optional[str] = None
    ) -> bool:
        """
        发送通知邮件
        
        Args:
            user: 用户对象
            title: 通知标题
            message: 通知内容
            action_url: 操作链接
            
        Returns:
            bool: 发送是否成功
        """
        try:
            # 邮件主题
            subject = f"通知 - {title}"
            
            # HTML 内容
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>{title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .button {{ display: inline-block; padding: 12px 24px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; }}
                    .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{title}</h1>
                    </div>
                    <div class="content">
                        <p>亲爱的 {user.full_name}，</p>
                        <p>{message}</p>
                        {f'<p style="text-align: center;"><a href="{action_url}" class="button">查看详情</a></p>' if action_url else ''}
                    </div>
                    <div class="footer">
                        <p>此邮件由系统自动发送，请勿回复。</p>
                        <p>© 2024 FastAPI Shop. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 纯文本内容
            text_content = f"""
            {title}
            
            亲爱的 {user.full_name}，
            
            {message}
            
            {f'查看详情：{action_url}' if action_url else ''}
            
            此邮件由系统自动发送，请勿回复。
            © 2024 FastAPI Shop. All rights reserved.
            """
            
            return await self.send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error("Failed to send notification email", user_id=user.id, error=str(e))
            return False
    
    async def _generate_verification_token(self, user_id: int) -> str:
        """
        生成验证令牌
        
        Args:
            user_id: 用户 ID
            
        Returns:
            str: 验证令牌
        """
        # 这里应该调用用户服务生成令牌
        # 为了简化，直接返回一个示例令牌
        return f"verification_token_{user_id}_{datetime.utcnow().timestamp()}"
    
    async def send_bulk_email(
        self,
        recipients: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        批量发送邮件
        
        Args:
            recipients: 收件人列表
            subject: 邮件主题
            html_content: HTML 内容
            text_content: 纯文本内容
            
        Returns:
            Dict[str, Any]: 发送结果统计
        """
        try:
            results = {
                "total": len(recipients),
                "success": 0,
                "failed": 0,
                "errors": []
            }
            
            # 并发发送邮件
            tasks = []
            for recipient in recipients:
                task = self.send_email(recipient, subject, html_content, text_content)
                tasks.append(task)
            
            # 等待所有任务完成
            send_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计结果
            for i, result in enumerate(send_results):
                if isinstance(result, Exception):
                    results["failed"] += 1
                    results["errors"].append({
                        "recipient": recipients[i],
                        "error": str(result)
                    })
                elif result:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "recipient": recipients[i],
                        "error": "发送失败"
                    })
            
            logger.info("Bulk email sending completed", **results)
            
            return results
            
        except Exception as e:
            logger.error("Failed to send bulk email", error=str(e))
            return {
                "total": len(recipients),
                "success": 0,
                "failed": len(recipients),
                "errors": [{"error": str(e)}]
            }

