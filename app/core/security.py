"""
安全工具模块
============

提供密码加密、JWT令牌生成和验证等安全相关功能。
支持用户认证、权限控制、令牌刷新等操作。

设计思路:
1. 使用 bcrypt 进行密码加密
2. 使用 PyJWT 进行 JWT 令牌生成和验证
3. 支持访问令牌和刷新令牌
4. 集成 Redis 进行令牌黑名单管理
5. 提供权限验证装饰器

主要组件和调用关系:
1. 密码处理函数:
   - get_password_hash(): 使用 bcrypt 对密码进行哈希处理
   - verify_password(): 验证明文密码与哈希密码是否匹配

2. JWT令牌处理函数:
   - create_access_token(): 创建访问令牌
   - create_refresh_token(): 创建刷新令牌
   - decode_token(): 解码 JWT 令牌
   - verify_token(): 验证 JWT 令牌有效性
   - create_tokens_for_user(): 为用户创建访问和刷新令牌对

3. 权限检查函数:
   - is_user_in_role(): 检查用户是否具有指定角色
   - get_current_user(): 获取当前认证用户（FastAPI依赖项）
   - get_current_active_user(): 获取当前活跃用户（FastAPI依赖项）
   - get_current_merchant(): 获取当前商家用户（FastAPI依赖项）
   - get_current_admin(): 获取当前管理员用户（FastAPI依赖项）
   - require_permission(): 权限检查装饰器工厂函数

4. 主要调用关系:
   - 认证流程: oauth2_scheme -> get_current_user -> get_user_by_id
   - 权限检查: require_permission -> permission_checker -> verify_token
   - 令牌创建: create_tokens_for_user -> create_access_token & create_refresh_token
"""

from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
import bcrypt
import jwt
from jwt import PyJWTError
import structlog

from .config import settings
from ..models.user import User, UserRole

# 配置日志
logger = structlog.get_logger(__name__)

# JWT 算法常量，从配置中获取
JWT_ALGORITHM = settings.algorithm
JWT_SECRET_KEY = settings.secret_key

# 令牌过期时间配置，从配置中获取
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码与哈希密码是否匹配
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码
        
    Returns:
        bool: 密码是否匹配
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        logger.error("Password verification error", error=str(e))
        return False


def get_password_hash(password: str) -> str:
    """
    对密码进行哈希处理
    
    Args:
        password: 明文密码
        
    Returns:
        str: 哈希后的密码
    """
    try:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error("Password hashing error", error=str(e))
        raise


def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建访问令牌
    
    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量
        
    Returns:
        str: JWT 访问令牌
    """
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error("Access token creation error", error=str(e))
        raise


def create_refresh_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建刷新令牌
    
    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量
        
    Returns:
        str: JWT 刷新令牌
    """
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error("Refresh token creation error", error=str(e))
        raise


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码 JWT 令牌
    
    Args:
        token: JWT 令牌
        
    Returns:
        Optional[Dict[str, Any]]: 解码后的数据，如果失败返回 None
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except PyJWTError as e:
        logger.warning("Token decode error", error=str(e))
        return None
    except Exception as e:
        logger.error("Unexpected token decode error", error=str(e))
        return None


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    验证 JWT 令牌
    
    Args:
        token: JWT 令牌
        
    Returns:
        Optional[Dict[str, Any]]: 验证后的数据，如果失败返回 None
    """
    payload = decode_token(token)
    if not payload:
        return None
    
    # 检查令牌类型
    if "type" not in payload:
        logger.warning("Token missing type", token=token)
        return None
    
    # 检查过期时间
    exp = payload.get("exp")
    if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
        logger.info("Token expired", token=token)
        return None
    
    return payload


def create_tokens_for_user(user: User) -> Dict[str, str]:
    """
    为用户创建访问令牌和刷新令牌
    
    Args:
        user: 用户对象
        
    Returns:
        Dict[str, str]: 包含访问令牌和刷新令牌的字典
    """
    try:
        # 访问令牌数据
        access_data = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value,
            "username": user.username
        }
        
        # 刷新令牌数据
        refresh_data = {
            "user_id": user.id,
            "email": user.email,
            "token_id": f"{user.id}-{int(datetime.utcnow().timestamp())}"
        }
        
        # 创建令牌
        access_token = create_access_token(
            data=access_data,
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        refresh_token = create_refresh_token(
            data=refresh_data,
            expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error("Token creation for user error", error=str(e), user_id=user.id)
        raise


def is_user_in_role(payload: Dict[str, Any], required_role: Union[str, UserRole]) -> bool:
    """
    检查用户是否具有指定角色
    
    Args:
        payload: JWT 令牌载荷
        required_role: 所需角色
        
    Returns:
        bool: 用户是否具有指定角色
    """
    if isinstance(required_role, UserRole):
        required_role = required_role.value
    
    user_role = payload.get("role")
    if not user_role:
        return False
    
    # 管理员具有所有权限
    if user_role == UserRole.ADMIN.value:
        return True
    
    return user_role == required_role


# 权限装饰器常量，定义各角色可访问的权限级别
PERMISSIONS = {
    "user": [UserRole.USER, UserRole.MERCHANT, UserRole.ADMIN],
    "merchant": [UserRole.MERCHANT, UserRole.ADMIN],
    "admin": [UserRole.ADMIN]
}


from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Tuple

from ..core.database import get_async_db
from ..models.user import User
from ..services.user_service import get_user_by_id


# OAuth2 密码流，用于从请求头中提取Bearer Token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db)
) -> User:
    """
    获取当前认证用户
    
    Args:
        token: JWT 令牌
        db: 数据库会话
        
    Returns:
        User: 当前用户对象
        
    Raises:
        HTTPException: 认证失败时抛出异常
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 验证令牌
    payload = verify_token(token)
    if not payload:
        raise credentials_exception
    
    # 获取用户ID
    user_id = payload.get("user_id")
    if not user_id:
        raise credentials_exception
    
    # 获取用户
    user = await get_user_by_id(db, user_id)
    if not user:
        raise credentials_exception
    
    # 检查用户状态
    if not user.is_active or user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive or deleted"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前活跃用户
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        User: 当前活跃用户对象
        
    Raises:
        HTTPException: 用户不活跃时抛出异常
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_merchant(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前商家用户
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        User: 当前商家用户对象
        
    Raises:
        HTTPException: 用户不是商家时抛出异常
    """
    if not current_user.is_merchant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Merchant access required"
        )
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前管理员用户
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        User: 当前管理员用户对象
        
    Raises:
        HTTPException: 用户不是管理员时抛出异常
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_permission(required_role: str):
    """
    权限检查装饰器
    
    Args:
        required_role: 所需角色
        
    Returns:
        callable: 依赖注入函数
    """
    async def permission_checker(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_async_db)
    ) -> Tuple[User, Dict[str, Any]]:
        """
        权限检查器
        
        Args:
            token: JWT 令牌
            db: 数据库会话
            
        Returns:
            Tuple[User, Dict[str, Any]]: 用户对象和令牌载荷
            
        Raises:
            HTTPException: 权限不足时抛出异常
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        # 验证令牌
        payload = verify_token(token)
        if not payload:
            raise credentials_exception
        
        # 检查角色权限
        if required_role not in PERMISSIONS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid permission requirement"
            )
        
        allowed_roles = PERMISSIONS[required_role]
        user_role = payload.get("role")
        if not user_role or UserRole(user_role) not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{required_role} permission required"
            )
        
        # 获取用户
        user_id = payload.get("user_id")
        if not user_id:
            raise credentials_exception
        
        user = await get_user_by_id(db, user_id)
        if not user:
            raise credentials_exception
        
        # 检查用户状态
        if not user.is_active or user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive or deleted"
            )
        
        return user, payload
    
    return permission_checker