"""
认证相关Schema
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, description="密码")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "password123"
            }
        }


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, description="密码")
    email: Optional[str] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "newuser",
                "password": "password123",
                "email": "user@example.com",
                "full_name": "新用户"
            }
        }


class LoginResponse(BaseModel):
    """登录响应"""
    user: dict
    token: str
    session_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "id": 1,
                    "username": "admin",
                    "full_name": "管理员",
                    "is_superadmin": True
                },
                "token": "eyJhbGc...",
                "session_id": "xxx"
            }
        }


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)


class UserInfo(BaseModel):
    """用户信息"""
    id: int
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    is_superadmin: bool
    is_active: bool
    current_project: Optional[dict] = None
    permissions: List[str] = []
    
    class Config:
        from_attributes = True


class TokenData(BaseModel):
    """Token数据（简化版，移除project_id）"""
    user_id: Optional[int] = None
    type: Optional[str] = None
    purpose: Optional[str] = None

