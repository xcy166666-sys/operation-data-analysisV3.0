"""
FastAPI应用入口（运营数据分析系统）
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, OperationalError
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from app.core.config import settings
from app.core.redis import redis_client
from app.middleware.logging_middleware import logging_middleware
from app.middleware.error_handler import (
    error_handler_middleware,
    validation_exception_handler,
    integrity_error_handler,
    operational_error_handler
)
from app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info(f"启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"调试模式: {settings.DEBUG}")
    
    # 连接Redis
    try:
        await redis_client.connect()
        logger.info("✅ Redis连接成功")
    except Exception as e:
        logger.error(f"❌ Redis连接失败: {e}")
    
    yield
    
    # 关闭时执行
    logger.info("正在关闭应用...")
    
    # 断开Redis连接
    try:
        await redis_client.disconnect()
        logger.info("✅ Redis已断开")
    except Exception as e:
        logger.error(f"❌ Redis断开失败: {e}")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="运营数据分析系统API",
    lifespan=lifespan,
    docs_url="/docs",  # 始终启用API文档
    redoc_url="/redoc",  # 始终启用ReDoc文档
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 日志中间件
app.middleware("http")(logging_middleware)

# 错误处理中间件
app.middleware("http")(error_handler_middleware)

# 异常处理器
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(OperationalError, operational_error_handler)

# 注册API路由
app.include_router(api_router, prefix="/api/v1")


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

