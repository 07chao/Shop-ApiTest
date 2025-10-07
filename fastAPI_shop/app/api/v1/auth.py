"""
认证路由
========

实现用户认证相关的 API 端点，包括登录、注册、令牌刷新等。
支持 JWT 认证、密码重置、邮箱验证等功能。

设计思路:
1. 使用 OAuth2 密码模式进行认证
2. 实现访问令牌和刷新令牌机制
3. 支持密码重置和邮箱验证
4. 包含令牌黑名单功能
5. 提供安全的登出机制
6. 支持多角色权限控制
"""

from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from ...core.database import get_async_db
from ...core.security import (
    authenticate_user,
    create_user_tokens,
    verify_token,
    add_token_to_blacklist,
    get_password_hash
)
from ...core.config import settings
from ...models.user import User
from ...schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    PasswordReset,
    PasswordResetConfirm,
    EmailVerification
)
from ...services.user_service import UserService
from ...services.email_service import EmailService

# 配置日志
logger = structlog.get_logger(__name__)

# 创建路由
router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    用户注册
    
    创建新用户账户，发送验证邮件。
    """
    try:
        user_service = UserService(db)
        
        # 检查邮箱是否已存在
        existing_user = await user_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
        
        # 检查用户名是否已存在
        if user_data.username:
            existing_username = await user_service.get_user_by_username(user_data.username)
            if existing_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户名已被使用"
                )
        
        # 创建用户
        user = await user_service.create_user(user_data)
        
        # 发送验证邮件
        email_service = EmailService()
        await email_service.send_verification_email(user)
        
        logger.info("User registered successfully", user_id=user.id, email=user.email)
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("User registration failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    用户登录
    
    验证用户凭据，返回访问令牌和刷新令牌。
    """
    try:
        # 验证用户凭据
        user = await authenticate_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 检查用户状态
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="账户已被禁用"
            )
        
        # 创建令牌
        tokens = await create_user_tokens(user)
        
        # 更新最后登录时间
        user_service = UserService(db)
        await user_service.update_last_login(user.id)
        
        logger.info("User logged in successfully", user_id=user.id, email=user.email)
        
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("User login failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    刷新访问令牌
    
    使用刷新令牌获取新的访问令牌。
    """
    try:
        # 验证刷新令牌
        token_data = await verify_token(refresh_token, "refresh")
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌"
            )
        
        # 获取用户信息
        user_service = UserService(db)
        user = await user_service.get_user_by_id(token_data.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已被禁用"
            )
        
        # 创建新的令牌
        tokens = await create_user_tokens(user)
        
        # 将旧的刷新令牌加入黑名单
        await add_token_to_blacklist(refresh_token)
        
        logger.info("Token refreshed successfully", user_id=user.id)
        
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌刷新失败"
        )


@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme)
) -> Any:
    """
    用户登出
    
    将访问令牌加入黑名单。
    """
    try:
        # 将令牌加入黑名单
        await add_token_to_blacklist(token)
        
        logger.info("User logged out successfully")
        
        return {"message": "登出成功"}
        
    except Exception as e:
        logger.error("User logout failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出失败"
        )


@router.post("/password-reset")
async def request_password_reset(
    password_reset: PasswordReset,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    请求密码重置
    
    发送密码重置邮件。
    """
    try:
        user_service = UserService(db)
        user = await user_service.get_user_by_email(password_reset.email)
        
        if user and user.is_active:
            # 生成重置令牌
            reset_token = await user_service.generate_password_reset_token(user.id)
            
            # 发送重置邮件
            email_service = EmailService()
            await email_service.send_password_reset_email(user, reset_token)
            
            logger.info("Password reset email sent", user_id=user.id, email=user.email)
        
        # 无论用户是否存在，都返回成功消息（安全考虑）
        return {"message": "如果邮箱存在，密码重置邮件已发送"}
        
    except Exception as e:
        logger.error("Password reset request failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码重置请求失败"
        )


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    password_reset_confirm: PasswordResetConfirm,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    确认密码重置
    
    使用重置令牌设置新密码。
    """
    try:
        user_service = UserService(db)
        
        # 验证重置令牌
        user_id = await user_service.verify_password_reset_token(
            password_reset_confirm.token
        )
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效或过期的重置令牌"
            )
        
        # 更新密码
        await user_service.update_password(
            user_id, 
            password_reset_confirm.new_password
        )
        
        logger.info("Password reset completed", user_id=user_id)
        
        return {"message": "密码重置成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Password reset confirmation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码重置确认失败"
        )


@router.post("/email-verification")
async def verify_email(
    email_verification: EmailVerification,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    邮箱验证
    
    验证用户邮箱地址。
    """
    try:
        user_service = UserService(db)
        
        # 验证邮箱验证令牌
        user_id = await user_service.verify_email_token(email_verification.token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效或过期的验证令牌"
            )
        
        # 标记邮箱为已验证
        await user_service.mark_email_verified(user_id)
        
        logger.info("Email verified successfully", user_id=user_id)
        
        return {"message": "邮箱验证成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Email verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="邮箱验证失败"
        )


@router.post("/resend-verification")
async def resend_verification(
    email: str,
    db: AsyncSession = Depends(get_async_db)
) -> Any:
    """
    重新发送验证邮件
    
    为未验证的用户重新发送验证邮件。
    """
    try:
        user_service = UserService(db)
        user = await user_service.get_user_by_email(email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已验证"
            )
        
        # 发送验证邮件
        email_service = EmailService()
        await email_service.send_verification_email(user)
        
        logger.info("Verification email resent", user_id=user.id, email=user.email)
        
        return {"message": "验证邮件已重新发送"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Resend verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重新发送验证邮件失败"
        )

