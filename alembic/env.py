"""
Alembic 环境配置
================

配置 Alembic 数据库迁移环境，支持异步数据库操作。
包含迁移脚本生成、数据库连接、模型导入等功能。

设计思路:
1. 使用异步 SQLAlchemy 引擎
2. 自动导入所有模型
3. 支持环境变量配置
4. 包含迁移脚本模板
5. 支持多数据库环境
6. 集成应用配置
"""

import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 导入应用配置和模型
from app.core.config import settings
from app.core.database import Base
from app.models import *  # 导入所有模型

# Alembic 配置对象
config = context.config

# 设置数据库 URL
config.set_main_option("sqlalchemy.url", settings.database_url_sync)

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 目标元数据
target_metadata = Base.metadata

# 其他配置
config.set_main_option("sqlalchemy.url", settings.database_url_sync)


def run_migrations_offline() -> None:
    """
    离线模式运行迁移
    
    生成 SQL 脚本而不连接到数据库
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    执行迁移
    
    Args:
        connection: 数据库连接
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    异步模式运行迁移
    
    连接到数据库并执行迁移
    """
    # 创建异步引擎配置
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.database_url
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    在线模式运行迁移
    
    连接到数据库并执行迁移
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

