# FastAPI Shop - 智能电商平台

一个基于 FastAPI + PostgreSQL + Redis + Celery 的现代化电商后端骨架，内置 JWT 认证、商品/库存/订单/支付（模拟）、AI 辅助（RAG/向量检索）、监控与容器化部署（Docker Compose）。

## 特性
- 认证：OAuth2 密码模式 + JWT（Access/Refresh），角色 `user/merchant/admin`
- 数据：PostgreSQL（JSONB/索引），SQLAlchemy 2.0 异步 ORM + Alembic 迁移
- 缓存/并发：Redis（缓存、分布式锁、队列键空间）
- 异步：Celery（Worker/Beat/Flower 监控）
- AI/RAG：LangChain + 向量检索（可接 Milvus/Weaviate/Pinecone）
- 搜索：Elasticsearch + Kibana（可选）
- 监控：Prometheus + Grafana（可选）
- 部署：Dockerfile + docker-compose 一键起服务

---

## 快速开始（本地 Docker Compose）
1. 克隆并进入目录
```bash
git clone <your-repo>
cd fastapi_shop_
```
2. 准备环境变量（可选）
```bash
cp env.example .env
```
3. 启动依赖与应用
```bash
docker compose up -d --build
```
4. 访问服务
- API: http://localhost:8000
- OpenAPI 文档（开发模式）: http://localhost:8000/docs
- Flower（Celery 监控）: http://localhost:5555
- Elasticsearch: http://localhost:9200 （可选）
- Kibana: http://localhost:5601 （可选）
- Prometheus: http://localhost:9090 （可选）
- Grafana: http://localhost:3000 （可选，默认密码 admin/admin）

5. 关闭
```bash
docker compose down -v
```

> 首次启动会自动创建表结构；生产环境建议只用 Alembic 管理迁移。

---

## 手动运行（本机 Python 环境）
1. Python 3.11+，安装依赖
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```
2. 配置环境变量
```bash
cp env.example .env
```
3. 运行应用
```bash
uvicorn app.main:app --reload
```

---

## 数据库迁移（Alembic）
- 初始化（已配置 `alembic/`）
```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```
- 常用命令
```bash
alembic current
alembic history
alembic downgrade -1
```

---

## 项目结构

```
.
├── alembic/                 # 数据库迁移文件
├── app/                     # 后端应用代码
│   ├── api/                 # API路由
│   ├── core/                # 核心配置和工具
│   ├── models/              # 数据模型
│   ├── schemas/             # 数据验证模型
│   ├── services/            # 业务逻辑
│   ├── tasks/               # 异步任务
│   └── main.py             # 应用入口
├── frontend/                # 前端应用代码
│   ├── public/              # 静态资源
│   ├── src/                 # 源代码
│   │   ├── assets/          # 静态资源
│   │   ├── components/      # 公共组件
│   │   ├── views/           # 页面组件
│   │   ├── services/        # API服务
│   │   ├── utils/           # 工具函数
│   │   ├── router/          # 路由配置
│   │   ├── store/           # 状态管理
│   │   ├── App.jsx          # 根组件
│   │   └── main.jsx         # 入口文件
│   ├── package.json         # 前端依赖
│   └── vite.config.js       # 构建配置
├── monitoring/              # 监控配置
├── nginx/                   # Nginx配置
├── tests/                   # 测试文件
├── docker-compose.yml       # Docker编排文件
├── Dockerfile               # 后端Docker配置
└── requirements.txt         # Python依赖
```

---

## 环境变量（.env）
见 `env.example`，关键项：
- 数据库：`DATABASE_URL`、`DATABASE_URL_SYNC`
- Redis：`REDIS_URL`
- JWT：`SECRET_KEY`、`ACCESS_TOKEN_EXPIRE_MINUTES`、`REFRESH_TOKEN_EXPIRE_DAYS`
- OpenAI（可选）：`OPENAI_API_KEY`、`OPENAI_MODEL`、`EMBEDDING_MODEL`
- Celery：`CELERY_BROKER_URL`、`CELERY_RESULT_BACKEND`
- CORS：`CORS_ORIGINS`

---

## 运行方式
- Docker（推荐开发体验）
```bash
docker compose up -d --build
```
- 本机
```bash
uvicorn app.main:app --reload --port 8000
```

---

## 核心模块概览
- 认证与权限：`app/core/security.py`、`app/api/v1/auth.py`
  - 登录返回 Access/Refresh；刷新会将旧 Refresh 加入 Redis 黑名单
- 数据与迁移：`app/core/database.py`、`alembic/`
- 业务模型：`app/models/*`（JSONB/ARRAY/索引已设计，满足电商扩展性）
- 服务层：`app/services/*`（如 `UserService`、`EmailService`）
- 路由分层：`app/api/v1/*`（后续可补齐 users/products/orders 等）

---

## Celery 与异步任务
服务包含：`celery_worker`、`celery_beat`、`flower`
- Worker：处理异步任务（图片、邮件、embedding、库存回滚等）
- Beat：定时任务调度
- Flower：队列监控（:5555）

> 注意：示例使用 Redis 作为 broker/backends，生产可用 RabbitMQ/Redis Cluster。

---

## AI/RAG（可选模块）
- 依赖：`langchain`、`openai`、`sentence-transformers`
- 典型流程：商品文本 → 嵌入 → 向量库 → 相似检索 → 业务过滤 → LLM 解释
- 配置：设置 `OPENAI_API_KEY`，可替换为本地模型/其他向量库

---

## 监控与日志
- 结构化日志：`structlog`
- Prometheus/Grafana（可选）：已在 compose 中预置服务与目录
- 健康检查：`GET /health`
- 指标：`GET /metrics`（可扩展为Prometheus格式）

---

## 常见问题（FAQ）
- 端口冲突？修改 `docker-compose.yml` 或本机端口占用
- 数据库无法连接？确认 `DATABASE_URL*` 与容器网络，或本机 Postgres 是否启动
- 无法访问 `/docs`？仅在 `DEBUG=True` 时开启
- 邮件发送失败？本地 SMTP 多受限，建议使用真实 SMTP 或禁用邮件相关逻辑

---

## 开发指南

### 后端开发

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 运行开发服务器：
   ```bash
   uvicorn app.main:app --reload
   ```

3. 运行数据库迁移：
   ```bash
   alembic upgrade head
   ```

### 前端开发

1. 进入前端目录：
   ```bash
   cd frontend
   ```

2. 安装依赖：
   ```bash
   npm install
   ```

3. 运行开发服务器：
   ```bash
   npm run dev
   ```

4. 构建生产版本：
   ```bash
   npm run build
   ```

### 使用Docker进行开发

1. 启动所有服务：
   ```bash
   docker-compose up -d
   ```

2. 查看服务状态：
   ```bash
   docker-compose ps
   ```

3. 查看日志：
   ```bash
   docker-compose logs -f [service_name]
   ```

4. 停止所有服务：
   ```bash
   docker-compose down
   ```

## API文档

访问 `http://localhost:8000/docs` 查看自动生成的API文档。

## 前端访问

访问 `http://localhost:3000` 使用前端界面。

## 许可证
MIT
