"""
全局错误处理中间件
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, OperationalError
from loguru import logger


async def error_handler_middleware(request: Request, call_next):
    """全局错误处理中间件"""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"未捕获的异常: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "SERVER_ERROR",
                    "message": "服务器内部错误",
                    "details": str(e) if logger.level("DEBUG").no >= logger._core.min_level else None
                }
            }
        )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """参数验证错误处理"""
    logger.error(f"=== 参数验证错误 ===")
    logger.error(f"URL: {request.url}")
    logger.error(f"Method: {request.method}")
    logger.error(f"Errors: {exc.errors()}")
    logger.error(f"Body: {exc.body}")
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": "输入参数错误",
                "details": exc.errors()
            }
        }
    )


async def integrity_error_handler(request: Request, exc: IntegrityError):
    """数据库完整性错误处理"""
    logger.error(f"数据库完整性错误: {exc}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "success": False,
            "error": {
                "code": "ALREADY_EXISTS",
                "message": "数据已存在或违反约束条件",
                "details": str(exc.orig) if hasattr(exc, 'orig') else str(exc)
            }
        }
    )


async def operational_error_handler(request: Request, exc: OperationalError):
    """数据库操作错误处理"""
    logger.error(f"数据库操作错误: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "DATABASE_ERROR",
                "message": "数据库操作失败",
                "details": None
            }
        }
    )

