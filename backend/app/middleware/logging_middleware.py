"""
日志中间件
"""
import time
from fastapi import Request
from loguru import logger


async def logging_middleware(request: Request, call_next):
    """请求日志中间件"""
    # 过滤掉health检查请求的日志
    is_health_check = request.url.path == "/health"
    
    # 开始时间
    start_time = time.time()
    
    # 记录请求（排除health检查）
    if not is_health_check:
        logger.info(
            f"请求开始: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
    
    # 处理请求
    response = await call_next(request)
    
    # 计算耗时
    process_time = time.time() - start_time
    
    # 记录响应（排除health检查）
    if not is_health_check:
        logger.info(
            f"请求完成: {request.method} {request.url.path} "
            f"status={response.status_code} time={process_time:.3f}s"
        )
    
    # 添加响应头
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

