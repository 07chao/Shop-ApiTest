"""
数据库连接和会话管理
==================

使用 SQLAlchemy 2.0 的异步特性，提供数据库连接池和会话管理。
支持 PostgreSQL 作为主数据库，包含连接池配置和健康检查。

设计思路:
1. 使用 asyncpg 驱动提供高性能异步数据库访问
2. 配置连接池以优化并发性能
3. 提供同步和异步两种数据库会话
4. 支持数据库健康检查和自动重连
5. 集成 Alembic 进行数据库迁移管理
"""

from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import structlog

from .config import settings

# 配置日志
logger = structlog.get_logger(__name__)

# 创建数据库基础模型类
Base = declarative_base()

# 配置元数据，用于表名和约束命名
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)

# 异步数据库引擎配置
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # 开发环境下打印SQL语句
    poolclass=QueuePool,
    pool_size=20,  # 连接池大小
    max_overflow=30,  # 最大溢出连接数
    pool_pre_ping=True,  # 连接前检查连接是否有效
    pool_recycle=3600,  # 连接回收时间(秒)
    connect_args={
        "server_settings": {
            "application_name": "fastapi_shop",
        }
    }
)

# 同步数据库引擎配置（用于 Alembic 迁移）
sync_engine = create_engine(
    settings.database_url_sync,
    echo=settings.debug,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 提交后不使对象过期
    autoflush=True,  # 自动刷新
    autocommit=False,  # 手动提交
)

# 同步会话工厂
SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库会话的依赖注入函数
    
    使用方式:
    @router.get("/")
    async def endpoint(db: AsyncSession = Depends(get_async_db)):
        # 使用 db 进行数据库操作
        pass
    
    Yields:
        AsyncSession: 异步数据库会话
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # 自动提交事务
        except Exception as e:
            await session.rollback()  # 发生异常时回滚
            logger.error("Database session error", error=str(e))
            raise
        finally:
            await session.close()  # 确保会话关闭


def get_db() -> Generator[Session, None, None]:
    """
    获取同步数据库会话的依赖注入函数
    
    主要用于 Alembic 迁移和同步操作
    
    Yields:
        Session: 同步数据库会话
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Database session error", error=str(e))
        raise
    finally:
        db.close()


async def init_db() -> None:
    """
    初始化数据库
    
    创建所有表结构，用于应用启动时的数据库初始化
    """
    try:
        async with async_engine.begin() as conn:
            # 创建所有表
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


async def check_db_health() -> bool:
    """
    检查数据库连接健康状态
    
    Returns:
        bool: 数据库是否健康
    """
    try:
        async with async_engine.begin() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False


async def close_db() -> None:
    """
    关闭数据库连接
    
    用于应用关闭时清理资源
    """
    try:
        await async_engine.dispose()
        sync_engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error("Error closing database connections", error=str(e))

