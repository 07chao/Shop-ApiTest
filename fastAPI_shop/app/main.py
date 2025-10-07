"""
FastAPI 应用主入口
==================

创建和配置 FastAPI 应用，包含中间件、路由、异常处理等。
支持 CORS、请求日志、性能监控等功能。

设计思路:
1. 使用 FastAPI 创建应用实例
2. 配置中间件（CORS、日志、性能监控）
3. 注册 API 路由
4. 设置异常处理器
5. 支持应用生命周期事件
6. 集成健康检查端点
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import structlog
import time
import uvicorn

from .core.config import settings
from .core.database import init_db, close_db, check_db_health
from .core.exceptions import FastAPIShopException, create_http_exception
from .api import api_router

# 配置结构化日志
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    处理应用启动和关闭事件
    """
    # 启动事件
    logger.info("Starting FastAPI Shop application")
    
    try:
        # 初始化数据库
        await init_db()
        logger.info("Database initialized successfully")
        
        # 检查数据库健康状态
        db_healthy = await check_db_health()
        if not db_healthy:
            logger.warning("Database health check failed")
        
        logger.info("Application startup completed")
        
    except Exception as e:
        logger.error("Application startup failed", error=str(e))
        raise
    
    yield
    
    # 关闭事件
    logger.info("Shutting down FastAPI Shop application")
    
    try:
        # 关闭数据库连接
        await close_db()
        logger.info("Database connections closed")
        
        logger.info("Application shutdown completed")
        
    except Exception as e:
        logger.error("Application shutdown failed", error=str(e))


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="智能电商平台 - 基于FastAPI的现代化电商解决方案",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan
)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置 可信主机 中间件
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    请求日志中间件
    
    记录所有 HTTP 请求的详细信息
    """
    start_time = time.time()
    
    # 记录请求信息
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    # 处理请求
    response = await call_next(request)
    
    # 计算处理时间
    process_time = time.time() - start_time
    
    # 记录响应信息
    logger.info(
        "Request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=round(process_time, 4)
    )
    
    # 添加处理时间头
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    安全头中间件
    
    添加安全相关的 HTTP 头
    """
    response = await call_next(request)
    
    # 添加安全头
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response


# 注册 API 路由
app.include_router(api_router)

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """
    根路径
    
    返回应用基本信息
    """
    return {
        "message": "Welcome to FastAPI Shop",
        "version": settings.version,
        "environment": settings.environment,
        "docs_url": "/docs" if settings.debug else None
    }


@app.get("/health")
async def health_check():
    """
    健康检查端点
    
    检查应用和数据库的健康状态
    """
    try:
        # 检查数据库健康状态
        db_healthy = await check_db_health()
        
        health_status = {
            "status": "healthy" if db_healthy else "unhealthy",
            "timestamp": time.time(),
            "version": settings.version,
            "environment": settings.environment,
            "database": "connected" if db_healthy else "disconnected"
        }
        
        status_code = 200 if db_healthy else 503
        
        return JSONResponse(content=health_status, status_code=status_code)
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            content={
                "status": "unhealthy",
                "timestamp": time.time(),
                "error": str(e)
            },
            status_code=503
        )


@app.get("/metrics")
async def metrics():
    """
    指标端点
    
    返回应用性能指标（用于 Prometheus 监控）
    """
    # 这里可以添加更多指标
    return {
        "app_name": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "uptime": time.time()  # 简化处理，实际应该计算真实运行时间
    }


@app.exception_handler(FastAPIShopException)
async def fastapi_shop_exception_handler(request: Request, exc: FastAPIShopException):
    """
    应用异常处理器
    
    处理自定义业务异常
    """
    logger.error(
        "Application exception occurred",
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        url=str(request.url),
        method=request.method
    )
    
    return create_http_exception(exc)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTP 异常处理器
    
    处理 FastAPI HTTP 异常
    """
    logger.warning(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        url=str(request.url),
        method=request.method
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": "HTTP_ERROR",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    通用异常处理器
    
    处理未捕获的异常
    """
    logger.error(
        "Unhandled exception occurred",
        exception_type=type(exc).__name__,
        message=str(exc),
        url=str(request.url),
        method=request.method,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "内部服务器错误" if settings.is_production else str(exc),
            "status_code": 500
        }
    )


# 开发环境下的调试端点
if settings.debug:
    @app.get("/debug/info")
    async def debug_info():
        """
        调试信息端点
        
        返回应用配置和状态信息
        """
        return {
            "app_name": settings.app_name,
            "version": settings.version,
            "environment": settings.environment,
            "debug": settings.debug,
            "database_url": settings.database_url.split("@")[-1] if "@" in settings.database_url else "hidden",
            "redis_url": settings.redis_url,
            "cors_origins": settings.cors_origins
        }


if __name__ == "__main__":
    # 开发环境直接运行
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning"
    )

