"""
工作流模型（运营数据分析独立版）
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class Workflow(Base):
    """工作流配置表（简化版，移除项目依赖）"""
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False, default='operation')  # operation
    platform = Column(String(20), nullable=False)  # dify/langchain/ragflow
    config = Column(JSONB, nullable=False)  # API配置
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        CheckConstraint("platform IN ('dify', 'langchain', 'ragflow')", name='workflows_platform_check'),
    )
    
    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    binding = relationship("WorkflowBinding", back_populates="workflow", uselist=False, cascade="all, delete-orphan")
    sessions = relationship("AnalysisSession", back_populates="workflow")
    
    def __repr__(self):
        return f"<Workflow(id={self.id}, name='{self.name}', platform='{self.platform}')>"


class WorkflowBinding(Base):
    """工作流绑定表（支持用户级配置，user_id为None表示全局配置）"""
    __tablename__ = "workflow_bindings"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False)
    function_key = Column(String(50), nullable=False, default='operation_data_analysis')
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)  # 用户ID，None表示全局配置
    sheet_index = Column(Integer, nullable=True)  # Sheet索引（用于custom_operation_data_analysis，0-5对应6个工作流）
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    workflow = relationship("Workflow", back_populates="binding")
    user = relationship("User", foreign_keys=[user_id])
    
    # 唯一约束：每个用户每个功能键只能有一个工作流绑定
    # 对于custom_operation_data_analysis，需要加上sheet_index唯一性
    __table_args__ = (
        # 全局配置：user_id为None时，function_key必须唯一（如果sheet_index为None）
        # 对于custom_operation_data_analysis，需要(function_key, sheet_index)唯一
        # 用户配置：user_id不为None时，(user_id, function_key, sheet_index)必须唯一
    )
    
    def __repr__(self):
        return f"<WorkflowBinding(function_key='{self.function_key}', workflow_id={self.workflow_id}, user_id={self.user_id}, sheet_index={self.sheet_index})>"

