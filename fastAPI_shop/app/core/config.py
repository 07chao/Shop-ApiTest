"""
应用配置管理
============

使用 Pydantic Settings 管理应用配置，支持环境变量和配置文件。
包含数据库、Redis、JWT、AI、文件存储等所有配置项。

设计思路:
1. 使用 Pydantic BaseSettings 自动从环境变量读取配置
2. 支持 .env 文件进行本地开发配置
3. 提供配置验证和默认值
4. 区分开发、测试、生产环境
"""

from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    app_name: str = Field(default="FastAPI Shop", description="应用名称")
    version: str = Field(default="0.1.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    environment: str = Field(default="development", description="运行环境")
    
    # 数据库配置
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/fastapi_shop",
        description="异步数据库连接URL"
    )
    database_url_sync: str = Field(
        default="postgresql://user:password@localhost:5432/fastapi_shop",
        description="同步数据库连接URL"
    )
    
    # Redis 配置
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis 连接URL"
    )
    redis_password: Optional[str] = Field(default=None, description="Redis 密码")
    
    # JWT 配置
    secret_key: str = Field(
        default="your-secret-key-here-change-in-production",
        description="JWT 签名密钥"
    )
    algorithm: str = Field(default="HS256", description="JWT 算法")
    access_token_expire_minutes: int = Field(
        default=15,
        description="访问令牌过期时间(分钟)"
    )
    refresh_token_expire_days: int = Field(
        default=30,
        description="刷新令牌过期时间(天)"
    )
    
    # OpenAI 配置
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API 密钥")
    openai_model: str = Field(default="gpt-3.5-turbo", description="OpenAI 模型")
    embedding_model: str = Field(
        default="text-embedding-ada-002",
        description="嵌入模型"
    )
    
    # 文件存储配置
    upload_dir: str = Field(default="./uploads", description="文件上传目录")
    max_file_size: int = Field(default=10485760, description="最大文件大小(字节)")
    allowed_extensions: str = Field(
        default="jpg,jpeg,png,gif,webp",
        description="允许的文件扩展名"
    )
    
    # Celery 配置
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        description="Celery 消息代理URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        description="Celery 结果后端URL"
    )
    
    # 邮件配置
    smtp_host: Optional[str] = Field(default=None, description="SMTP 主机")
    smtp_port: int = Field(default=587, description="SMTP 端口")
    smtp_username: Optional[str] = Field(default=None, description="SMTP 用户名")
    smtp_password: Optional[str] = Field(default=None, description="SMTP 密码")
    
    # 监控配置
    prometheus_port: int = Field(default=8001, description="Prometheus 端口")
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN")
    
    # CORS 配置
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="CORS 允许的源"
    )
    
    # 向量数据库配置
    vector_db_url: str = Field(
        default="http://localhost:6333",
        description="向量数据库URL"
    )
    vector_db_api_key: Optional[str] = Field(
        default=None,
        description="向量数据库API密钥"
    )
    
    # 支付配置
    payment_gateway_url: str = Field(
        default="http://localhost:8000/api/v1/payments",
        description="支付网关URL"
    )
    payment_webhook_secret: str = Field(
        default="your-webhook-secret",
        description="支付回调密钥"
    )
    
    @validator("cors_origins", pre=True)
    def assemble_cors_origins(cls, v):
        """处理 CORS 源配置"""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @validator("allowed_extensions", pre=True)
    def assemble_allowed_extensions(cls, v):
        """处理允许的文件扩展名"""
        if isinstance(v, str):
            return [i.strip().lower() for i in v.split(",")]
        return v
    
    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment == "production"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例的依赖注入函数"""
    return settings

