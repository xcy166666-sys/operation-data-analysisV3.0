"""
功能模块相关Schema
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.schemas.workflow import WorkflowResponse


class FunctionModuleBase(BaseModel):
    """功能模块基础模型"""
    function_key: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    route_path: Optional[str] = Field(None, max_length=200)
    icon: Optional[str] = Field(None, max_length=50)
    category: str = Field(default="operation", max_length=50)
    is_enabled: bool = True
    sort_order: int = Field(default=0, ge=0)


class FunctionModuleCreate(FunctionModuleBase):
    """创建功能模块"""
    pass


class FunctionModuleUpdate(BaseModel):
    """更新功能模块"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    route_path: Optional[str] = Field(None, max_length=200)
    icon: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=50)
    is_enabled: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)


class FunctionModuleResponse(FunctionModuleBase):
    """功能模块响应"""
    id: int
    created_at: datetime
    updated_at: datetime
    workflow: Optional[WorkflowResponse] = None
    workflows: Optional[List[dict]] = None  # 用于定制化批量分析，包含多个工作流配置
    
    class Config:
        from_attributes = True


class FunctionConfigRequest(BaseModel):
    """功能API配置请求"""
    platform: str = Field(..., pattern="^(dify|langchain|ragflow)$")
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    config: dict = Field(..., description="API配置JSON")
    sheet_index: Optional[int] = Field(None, ge=0, le=5, description="Sheet索引（仅用于custom_operation_data_analysis，0-5）")


class CustomBatchWorkflowConfig(BaseModel):
    """单个工作流配置（用于定制化批量分析）"""
    sheet_index: int = Field(..., ge=0, le=5, description="Sheet索引（0-5）")
    platform: str = Field(..., pattern="^(dify|langchain|ragflow)$")
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    config: dict = Field(..., description="API配置JSON")


class CustomBatchConfigRequest(BaseModel):
    """定制化批量分析配置请求（包含6个工作流）"""
    workflows: List[CustomBatchWorkflowConfig] = Field(..., min_length=6, max_length=6, description="6个工作流配置列表，对应Sheet索引0-5")


class FunctionToggleRequest(BaseModel):
    """功能启用/禁用请求"""
    is_enabled: bool

