"""
API v1版本路由（简化版，仅包含运营数据分析相关路由）
"""
from fastapi import APIRouter

from app.api.v1 import auth, operation, workflow, users

api_router = APIRouter()

# 注册子路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(workflow.router, prefix="/workflows", tags=["工作流管理"])
api_router.include_router(operation.router, prefix="/operation", tags=["运营数据分析"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])

