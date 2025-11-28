"""
定制化批量分析模型（独立存储）
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class CustomBatchAnalysisSession(Base):
    """定制化批量分析会话表（独立存储）"""
    __tablename__ = "custom_batch_analysis_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    original_file_name = Column(String(255), nullable=False)
    original_file_path = Column(String(500), nullable=False)
    split_files_dir = Column(String(500), nullable=False)  # 拆分文件存储目录
    sheet_count = Column(Integer, nullable=False)  # Sheet总数
    status = Column(String(50), default='draft', nullable=False)  # draft, processing, completed, failed, partial_failed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'processing', 'completed', 'failed', 'partial_failed')", name='custom_batch_analysis_sessions_status_check'),
    )
    
    # 关系
    user = relationship("User", back_populates="custom_batch_analysis_sessions")
    custom_sheet_reports = relationship("CustomSheetReport", back_populates="custom_batch_session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CustomBatchAnalysisSession(id={self.id}, user_id={self.user_id}, sheet_count={self.sheet_count}, status='{self.status}')>"


class CustomSheetReport(Base):
    """定制化Sheet报告表（独立存储）"""
    __tablename__ = "custom_sheet_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    custom_batch_session_id = Column(Integer, ForeignKey('custom_batch_analysis_sessions.id', ondelete='CASCADE'), nullable=False)
    sheet_name = Column(String(255), nullable=False)  # Sheet名称
    sheet_index = Column(Integer, nullable=False)  # Sheet索引（从0开始）
    split_file_path = Column(String(500), nullable=False)  # 拆分后的文件路径
    report_content = Column(JSONB, nullable=True)  # 报告内容（text, charts, tables, metrics）
    report_status = Column(String(50), default='pending', nullable=False)  # pending, generating, completed, failed
    dify_conversation_id = Column(String(100), nullable=True)  # Dify对话ID（如果使用Chatflow）
    error_message = Column(Text, nullable=True)  # 错误信息（如果失败）
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        CheckConstraint("report_status IN ('pending', 'generating', 'completed', 'failed')", name='custom_sheet_reports_status_check'),
    )
    
    # 关系
    custom_batch_session = relationship("CustomBatchAnalysisSession", back_populates="custom_sheet_reports")
    
    def __repr__(self):
        return f"<CustomSheetReport(id={self.id}, custom_batch_session_id={self.custom_batch_session_id}, sheet_name='{self.sheet_name}', status='{self.report_status}')>"

