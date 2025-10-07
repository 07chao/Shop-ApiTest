"""
FastAPI 智能电商平台
==================

一个基于 FastAPI 的现代化电商解决方案，集成 AI 助手和智能推荐系统。

主要特性:
- 用户认证和权限管理
- 商品管理和库存系统
- 购物车和订单处理
- AI 智能助手 (RAG + Agent 工作流)
- 商家端智能上架工具
- 实时搜索和推荐
- 异步任务处理
- 监控和日志系统

架构设计:
- 后端: FastAPI + SQLAlchemy + Redis + Celery
- 数据库: PostgreSQL (主数据) + 向量数据库 (AI 检索)
- 前端: React + Ant Design (用户端/商家端)
- AI: LangChain + OpenAI + 向量检索
- 部署: Docker + Kubernetes
"""

__version__ = "0.1.0"
__author__ = "FastAPI Shop Team"

