"""
对话历史模型 - 用于持久化AI对话记录
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class DialogHistory(Base):
    """对话历史表 - 存储用户与AI的对话记录"""
    __tablename__ = "dialog_histories"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('analysis_sessions.id', ondelete='CASCADE'), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' | 'assistant' | 'system'
    content = Column(Text, nullable=False)

    # 版本标记：记录此消息是在哪个版本保存时产生的（用于时间轴显示）
    version_id = Column(Integer, ForeignKey('analysis_session_versions.id', ondelete='SET NULL'), nullable=True)

    # 额外数据：存储action_type、modified_charts、quoted_text等信息
    extra_data = Column(JSONB, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    session = relationship("AnalysisSession", back_populates="dialog_histories")
    version = relationship("AnalysisSessionVersion", backref="dialog_histories")

    # 索引：按session_id和时间排序查询
    __table_args__ = (
        Index('ix_dialog_histories_session_created', 'session_id', 'created_at'),
    )

    def __repr__(self):
        return f"<DialogHistory(id={self.id}, session_id={self.session_id}, role='{self.role}')>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "version_id": self.version_id,
            "extra_data": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "timestamp": self.created_at.isoformat() if self.created_at else None  # 兼容前端
        }
