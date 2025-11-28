"""
工作流相关Schema（简化版，移除项目依赖）
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class WorkflowBase(BaseModel):
    """工作流基础模型"""
    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., pattern="^(operation)$")  # 只支持operation
    platform: str = Field(..., pattern="^(dify|langchain|ragflow)$")  # 移除comfyui
    config: Dict[str, Any] = Field(..., description="API配置")
    description: Optional[str] = None
    is_active: bool = True


class WorkflowCreate(WorkflowBase):
    """创建工作流"""
    pass


class WorkflowUpdate(BaseModel):
    """更新工作流"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = Field(None, pattern="^(operation)$")
    platform: Optional[str] = Field(None, pattern="^(dify|langchain|ragflow)$")
    config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class WorkflowResponse(WorkflowBase):
    """工作流响应"""
    id: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FunctionWorkflowBind(BaseModel):
    """功能工作流绑定"""
    function_key: str = Field(..., min_length=1, max_length=50)
    workflow_id: int


class FunctionWorkflowResponse(BaseModel):
    """功能工作流响应（单项目系统，不需要project_id）"""
    id: int
    function_key: str
    workflow_id: int
    workflow: Optional[WorkflowResponse] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConversationMessage(BaseModel):
    """对话消息"""
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class ConversationCreate(BaseModel):
    """创建对话"""
    function_key: str
    workflow_id: Optional[int] = None
    title: Optional[str] = None
    messages: List[ConversationMessage] = []


class ConversationUpdate(BaseModel):
    """更新对话"""
    title: Optional[str] = None
    messages: Optional[List[ConversationMessage]] = None


class ConversationResponse(BaseModel):
    """对话响应"""
    id: int
    user_id: int
    project_id: int  # 保留字段，但固定为1
    function_key: str
    workflow_id: Optional[int]
    title: Optional[str]
    messages: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ExecuteWorkflowRequest(BaseModel):
    """执行工作流请求"""
    workflow_id: int  # 工作流ID
    function_key: str  # 功能键
    extra_inputs: Optional[Dict[str, Any]] = None  # 额外输入参数
    input: str  # 用户输入
    conversation_id: Optional[int] = None  # 对话ID（可选）


class ExecuteWorkflowResponse(BaseModel):
    """执行工作流响应"""
    execution_id: str  # 执行ID
    status: str  # 状态
    output: str  # AI输出

