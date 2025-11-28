"""
通用响应模型
"""
from typing import Generic, TypeVar, Optional, Any, List
from pydantic import BaseModel


T = TypeVar('T')


class ResponseBase(BaseModel):
    """基础响应模型"""
    success: bool
    message: Optional[str] = None


class SuccessResponse(ResponseBase, Generic[T]):
    """成功响应模型"""
    success: bool = True
    data: Optional[T] = None
    message: str = "操作成功"


class ErrorResponse(ResponseBase):
    """错误响应模型"""
    success: bool = False
    error: dict
    message: str = "操作失败"


class PaginationInfo(BaseModel):
    """分页信息"""
    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedData(BaseModel, Generic[T]):
    """分页数据模型"""
    items: List[T]
    pagination: PaginationInfo


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    success: bool = True
    data: PaginatedData[T]
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "items": [],
                    "pagination": {
                        "page": 1,
                        "page_size": 20,
                        "total": 100,
                        "total_pages": 5
                    }
                }
            }
        }

