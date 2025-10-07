"""
用户服务
========

提供用户相关的业务逻辑处理，包括用户注册、登录、信息管理等。
支持用户认证、权限控制、个人信息维护等操作。

设计思路:
1. 集成安全模块处理密码加密和令牌生成
2. 支持多种用户角色（客户、商家、管理员）
3. 提供用户信息验证和更新功能
4. 集成邮件服务发送验证邮件
5. 支持用户状态管理和权限控制
6. 提供用户统计和分析功能
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func
from sqlalchemy.exc import IntegrityError

from ..models.user import User, UserRole, UserStatus, Merchant
from ..models.address import Address
from ..core.security import get_password_hash, verify_password, create_tokens_for_user
from ..core.config import settings
from ..schemas.user import UserCreate, UserUpdate

# 配置日志
logger = structlog.get_logger(__name__)


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    根据用户ID获取用户
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        Optional[User]: 用户对象，如果未找到返回None
    """
    try:
        result = await db.execute(
            select(User)
            .options(selectinload(User.merchant))
            .where(User.id == user_id, User.is_deleted == False)
        )
        user = result.scalar_one_or_none()
        return user
        
    except Exception as e:
        logger.error("Get user by ID error", 
                    error=str(e), 
                    user_id=user_id)
        return None


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    根据邮箱获取用户
    
    Args:
        db: 数据库会话
        email: 用户邮箱
        
    Returns:
        Optional[User]: 用户对象，如果未找到返回None
    """
    try:
        result = await db.execute(
            select(User)
            .options(selectinload(User.merchant))
            .where(User.email == email, User.is_deleted == False)
        )
        user = result.scalar_one_or_none()
        return user
        
    except Exception as e:
        logger.error("Get user by email error", 
                    error=str(e), 
                    email=email)
        return None


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """
    用户认证
    
    Args:
        db: 数据库会话
        email: 用户邮箱
        password: 用户密码
        
    Returns:
        Optional[User]: 认证成功的用户对象，如果失败返回None
    """
    try:
        user = await get_user_by_email(db, email)
        if not user:
            logger.info("User not found", email=email)
            return None
        
        if not verify_password(password, user.password_hash):
            logger.info("Invalid password", email=email)
            return None
        
        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        await db.commit()
        
        return user
        
    except Exception as e:
        logger.error("Authenticate user error", 
                    error=str(e), 
                    email=email)
        return None


async def create_user(db: AsyncSession, user_data: UserCreate) -> Optional[User]:
    """
    创建用户
    
    Args:
        db: 数据库会话
        user_data: 用户创建数据
        
    Returns:
        Optional[User]: 创建的用户对象，如果失败返回None
    """
    try:
        async with db.begin():
            # 检查邮箱是否已存在
            existing_user = await get_user_by_email(db, user_data.email)
            if existing_user:
                logger.warning("Email already exists", email=user_data.email)
                return None
            
            # 检查用户名是否已存在
            if user_data.username:
                result = await db.execute(
                    select(User).where(User.username == user_data.username, User.is_deleted == False)
                )
                existing_username = result.scalar_one_or_none()
                if existing_username:
                    logger.warning("Username already exists", username=user_data.username)
                    return None
            
            # 创建用户
            user = User(
                email=user_data.email,
                username=user_data.username,
                phone=user_data.phone,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                bio=user_data.bio,
                password_hash=get_password_hash(user_data.password),
                role=user_data.role or UserRole.USER,
                status=UserStatus.PENDING,
                is_active=True,
                is_verified=False
            )
            
            db.add(user)
            await db.flush()  # 获取用户ID但不提交
            
            # 如果是商家，创建商家记录
            if user.role == UserRole.MERCHANT and hasattr(user_data, 'merchant_data') and user_data.merchant_data:
                merchant = Merchant(
                    user_id=user.id,
                    business_name=user_data.merchant_data.business_name,
                    contact_person=user_data.merchant_data.contact_person,
                    contact_phone=user_data.merchant_data.contact_phone
                )
                db.add(merchant)
            
            await db.commit()
            await db.refresh(user)
            
            logger.info("User created", 
                       user_id=user.id, 
                       email=user.email,
                       role=user.role.value)
            
            return user
            
    except IntegrityError as e:
        logger.warning("User creation integrity error", 
                      error=str(e), 
                      email=user_data.email)
        await db.rollback()
        return None
    except Exception as e:
        logger.error("User creation error", 
                    error=str(e), 
                    email=user_data.email)
        await db.rollback()
        return None


async def update_user(
    db: AsyncSession, 
    user_id: int, 
    user_data: UserUpdate
) -> Optional[User]:
    """
    更新用户信息
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        user_data: 用户更新数据
        
    Returns:
        Optional[User]: 更新后的用户对象，如果失败返回None
    """
    try:
        async with db.begin():
            # 获取用户
            user = await get_user_by_id(db, user_id)
            if not user:
                logger.warning("User not found", user_id=user_id)
                return None
            
            # 检查用户名是否已被其他用户使用
            if user_data.username and user_data.username != user.username:
                result = await db.execute(
                    select(User).where(User.username == user_data.username, User.is_deleted == False)
                )
                existing_username = result.scalar_one_or_none()
                if existing_username:
                    logger.warning("Username already exists", username=user_data.username)
                    return None
            
            # 更新用户信息
            update_data = user_data.dict(exclude_unset=True)
            
            # 处理密码更新
            if "password" in update_data:
                update_data["password_hash"] = get_password_hash(update_data.pop("password"))
            
            # 更新其他字段
            for field, value in update_data.items():
                if hasattr(user, field):
                    setattr(user, field, value)
            
            user.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(user)
            
            logger.info("User updated", 
                       user_id=user.id, 
                       updated_fields=list(update_data.keys()))
            
            return user
            
    except Exception as e:
        logger.error("User update error", 
                    error=str(e), 
                    user_id=user_id)
        await db.rollback()
        return None


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    """
    删除用户（软删除）
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        bool: 是否删除成功
    """
    try:
        async with db.begin():
            # 获取用户
            user = await get_user_by_id(db, user_id)
            if not user:
                logger.warning("User not found", user_id=user_id)
                return False
            
            # 软删除用户
            user.is_deleted = True
            user.deleted_at = datetime.utcnow()
            user.is_active = False
            user.updated_at = datetime.utcnow()
            
            await db.commit()
            
            logger.info("User deleted", user_id=user_id)
            
            return True
            
    except Exception as e:
        logger.error("User deletion error", 
                    error=str(e), 
                    user_id=user_id)
        await db.rollback()
        return False


async def activate_user(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    激活用户
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        Optional[User]: 激活后的用户对象，如果失败返回None
    """
    try:
        async with db.begin():
            # 获取用户
            user = await get_user_by_id(db, user_id)
            if not user:
                logger.warning("User not found", user_id=user_id)
                return None
            
            # 激活用户
            user.status = UserStatus.ACTIVE
            user.is_active = True
            user.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(user)
            
            logger.info("User activated", user_id=user_id)
            
            return user
            
    except Exception as e:
        logger.error("User activation error", 
                    error=str(e), 
                    user_id=user_id)
        await db.rollback()
        return None


async def deactivate_user(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    停用用户
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        Optional[User]: 停用后的用户对象，如果失败返回None
    """
    try:
        async with db.begin():
            # 获取用户
            user = await get_user_by_id(db, user_id)
            if not user:
                logger.warning("User not found", user_id=user_id)
                return None
            
            # 停用用户
            user.status = UserStatus.SUSPENDED
            user.is_active = False
            user.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(user)
            
            logger.info("User deactivated", user_id=user_id)
            
            return user
            
    except Exception as e:
        logger.error("User deactivation error", 
                    error=str(e), 
                    user_id=user_id)
        await db.rollback()
        return None


async def get_user_addresses(db: AsyncSession, user_id: int) -> List[Address]:
    """
    获取用户地址列表
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        
    Returns:
        List[Address]: 用户地址列表
    """
    try:
        result = await db.execute(
            select(Address)
            .where(Address.user_id == user_id)
            .where(Address.is_active == True)
            .order_by(Address.is_default.desc(), Address.created_at.desc())
        )
        addresses = result.scalars().all()
        return addresses
        
    except Exception as e:
        logger.error("Get user addresses error", 
                    error=str(e), 
                    user_id=user_id)
        return []


async def create_user_address(
    db: AsyncSession, 
    user_id: int, 
    address_data: Dict[str, Any]
) -> Optional[Address]:
    """
    创建用户地址
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        address_data: 地址数据
        
    Returns:
        Optional[Address]: 创建的地址对象，如果失败返回None
    """
    try:
        async with db.begin():
            # 如果是默认地址，取消其他默认地址
            if address_data.get("is_default", False):
                await db.execute(
                    update(Address)
                    .where(Address.user_id == user_id)
                    .values(is_default=False)
                )
            
            # 创建地址
            address = Address(
                user_id=user_id,
                **address_data
            )
            
            db.add(address)
            await db.commit()
            await db.refresh(address)
            
            logger.info("User address created", 
                       address_id=address.id, 
                       user_id=user_id)
            
            return address
            
    except Exception as e:
        logger.error("Create user address error", 
                    error=str(e), 
                    user_id=user_id)
        await db.rollback()
        return None


async def get_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None
) -> List[User]:
    """
    获取用户列表
    
    Args:
        db: 数据库会话
        skip: 跳过数量
        limit: 限制数量
        role: 用户角色过滤
        status: 用户状态过滤
        
    Returns:
        List[User]: 用户列表
    """
    try:
        query = select(User)
        
        # 添加过滤条件
        conditions = [User.is_deleted == False]
        if role:
            conditions.append(User.role == role)
        if status:
            conditions.append(User.status == status)
        
        query = query.where(and_(*conditions))
        
        # 添加分页和排序
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
        
        result = await db.execute(query)
        users = result.scalars().all()
        
        return users
        
    except Exception as e:
        logger.error("Get users error", 
                    error=str(e), 
                    skip=skip,
                    limit=limit)
        return []


async def get_user_count(
    db: AsyncSession,
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None
) -> int:
    """
    获取用户总数
    
    Args:
        db: 数据库会话
        role: 用户角色过滤
        status: 用户状态过滤
        
    Returns:
        int: 用户总数
    """
    try:
        query = select(func.count(User.id)).where(User.is_deleted == False)
        
        # 添加过滤条件
        if role:
            query = query.where(User.role == role)
        if status:
            query = query.where(User.status == status)
        
        result = await db.execute(query)
        count = result.scalar_one()
        
        return count
        
    except Exception as e:
        logger.error("Get user count error", 
                    error=str(e))
        return 0
