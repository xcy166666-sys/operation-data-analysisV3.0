"""
分析会话模型（运营数据分析独立版）
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class AnalysisSession(Base):
    """分析会话表（原Conversation，简化版）"""
    __tablename__ = "analysis_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    function_key = Column(String(50), default='operation_data_analysis', nullable=False)
    workflow_id = Column(Integer, ForeignKey('workflows.id', ondelete='SET NULL'), nullable=True)
    title = Column(String(200))
    messages = Column(JSONB, default=list, nullable=False)  # [{ role: 'user/assistant', content: '...' }]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    user = relationship("User", back_populates="analysis_sessions")
    workflow = relationship("Workflow", back_populates="sessions")
    versions = relationship("AnalysisSessionVersion", back_populates="session", cascade="all, delete-orphan")
    dialog_histories = relationship("DialogHistory", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AnalysisSession(id={self.id}, title='{self.title}', user_id={self.user_id})>"

