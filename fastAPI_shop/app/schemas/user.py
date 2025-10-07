"""
用户数据模式
============

定义用户相关的 Pydantic 模式，用于 API 请求和响应的数据验证。
包含用户注册、登录、更新、响应等模式。

设计思路:
1. 区分创建、更新、响应模式
2. 包含完整的字段验证规则
3. 支持密码强度验证
4. 包含角色和权限验证
5. 支持商家信息扩展
6. 提供安全的响应模式（隐藏敏感信息）
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator, ConfigDict
from enum import Enum

from ..models.user import UserRole, UserStatus


class UserRoleEnum(str, Enum):
    """用户角色枚举"""
    USER = "user"
    MERCHANT = "merchant"
    ADMIN = "admin"


class UserStatusEnum(str, Enum):
    """用户状态枚举"""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"


class UserBase(BaseModel):
    """用户基础模式"""
    email: EmailStr = Field(..., description="用户邮箱")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    phone: Optional[str] = Field(None, regex=r'^1[3-9]\d{9}$', description="手机号")
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, description="名")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, description="姓")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")


class UserCreate(UserBase):
    """用户创建模式"""
    password: str = Field(..., min_length=8, max_length=128, description="密码")
    role: UserRoleEnum = Field(default=UserRoleEnum.USER, description="用户角色")
    
    @validator('password')
    def validate_password(cls, v):
        """验证密码强度"""
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        """验证用户名"""
        if v and not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return v


class UserUpdate(BaseModel):
    """用户更新模式"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    phone: Optional[str] = Field(None, regex=r'^1[3-9]\d{9}$', description="手机号")
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, description="名")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, description="姓")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    avatar_url: Optional[str] = Field(None, max_length=500, description="头像URL")
    is_active: Optional[bool] = Field(None, description="是否激活")
    
    @validator('username')
    def validate_username(cls, v):
        """验证用户名"""
        if v and not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return v


class UserLogin(BaseModel):
    """用户登录模式"""
    email: EmailStr = Field(..., description="用户邮箱")
    password: str = Field(..., min_length=1, description="密码")


class UserResponse(UserBase):
    """用户响应模式"""
    id: int = Field(..., description="用户ID")
    role: UserRoleEnum = Field(..., description="用户角色")
    status: UserStatusEnum = Field(..., description="用户状态")
    is_active: bool = Field(..., description="是否激活")
    is_verified: bool = Field(..., description="是否已验证邮箱")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    
    model_config = ConfigDict(from_attributes=True)


class UserProfile(UserResponse):
    """用户详细资料模式"""
    profile_data: Optional[Dict[str, Any]] = Field(None, description="扩展个人信息")
    merchant: Optional['MerchantResponse'] = Field(None, description="商家信息")
    
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """令牌模式"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间(秒)")


class TokenData(BaseModel):
    """令牌数据模式"""
    user_id: int = Field(..., description="用户ID")
    role: Optional[str] = Field(None, description="用户角色")


class PasswordChange(BaseModel):
    """密码修改模式"""
    current_password: str = Field(..., min_length=1, description="当前密码")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密码")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """验证新密码强度"""
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v


class PasswordReset(BaseModel):
    """密码重置模式"""
    email: EmailStr = Field(..., description="用户邮箱")


class PasswordResetConfirm(BaseModel):
    """密码重置确认模式"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密码")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """验证新密码强度"""
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v


class EmailVerification(BaseModel):
    """邮箱验证模式"""
    token: str = Field(..., description="验证令牌")


class MerchantBase(BaseModel):
    """商家基础模式"""
    business_name: str = Field(..., min_length=2, max_length=200, description="商家名称")
    business_license: Optional[str] = Field(None, max_length=100, description="营业执照号")
    business_type: Optional[str] = Field(None, max_length=50, description="商家类型")
    contact_person: Optional[str] = Field(None, max_length=100, description="联系人")
    contact_phone: Optional[str] = Field(None, regex=r'^1[3-9]\d{9}$', description="联系电话")
    contact_email: Optional[EmailStr] = Field(None, description="联系邮箱")
    business_address: Optional[str] = Field(None, max_length=500, description="商家地址")
    business_city: Optional[str] = Field(None, max_length=50, description="所在城市")
    business_province: Optional[str] = Field(None, max_length=50, description="所在省份")
    delivery_radius: Optional[int] = Field(None, ge=0, le=100, description="配送半径(公里)")
    delivery_fee: Optional[float] = Field(None, ge=0, description="配送费")
    min_order_amount: Optional[float] = Field(None, ge=0, description="最低起送金额")


class MerchantCreate(MerchantBase):
    """商家创建模式"""
    pass


class MerchantUpdate(BaseModel):
    """商家更新模式"""
    business_name: Optional[str] = Field(None, min_length=2, max_length=200, description="商家名称")
    business_license: Optional[str] = Field(None, max_length=100, description="营业执照号")
    business_type: Optional[str] = Field(None, max_length=50, description="商家类型")
    contact_person: Optional[str] = Field(None, max_length=100, description="联系人")
    contact_phone: Optional[str] = Field(None, regex=r'^1[3-9]\d{9}$', description="联系电话")
    contact_email: Optional[EmailStr] = Field(None, description="联系邮箱")
    business_address: Optional[str] = Field(None, max_length=500, description="商家地址")
    business_city: Optional[str] = Field(None, max_length=50, description="所在城市")
    business_province: Optional[str] = Field(None, max_length=50, description="所在省份")
    delivery_radius: Optional[int] = Field(None, ge=0, le=100, description="配送半径(公里)")
    delivery_fee: Optional[float] = Field(None, ge=0, description="配送费")
    min_order_amount: Optional[float] = Field(None, ge=0, description="最低起送金额")
    is_verified: Optional[bool] = Field(None, description="是否已认证")
    is_active: Optional[bool] = Field(None, description="是否激活")


class MerchantResponse(MerchantBase):
    """商家响应模式"""
    id: int = Field(..., description="商家ID")
    user_id: int = Field(..., description="用户ID")
    is_verified: bool = Field(..., description="是否已认证")
    is_active: bool = Field(..., description="是否激活")
    business_data: Optional[Dict[str, Any]] = Field(None, description="商家扩展信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(from_attributes=True)


class UserList(BaseModel):
    """用户列表模式"""
    items: List[UserResponse] = Field(..., description="用户列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页数量")
    pages: int = Field(..., description="总页数")


class MerchantList(BaseModel):
    """商家列表模式"""
    items: List[MerchantResponse] = Field(..., description="商家列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页数量")
    pages: int = Field(..., description="总页数")

