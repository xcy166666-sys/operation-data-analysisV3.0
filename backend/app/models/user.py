"""
用户模型（运营数据分析独立版）
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, CheckConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100))
    full_name = Column(String(100))
    
    # 状态
    is_active = Column(Boolean, default=True, index=True)
    is_admin = Column(Boolean, default=False, comment="管理员标识")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    
    # 约束
    __table_args__ = (
        CheckConstraint("char_length(username) >= 3", name="username_length_check"),
    )
    
    # 关系
    analysis_sessions = relationship("AnalysisSession", back_populates="user", cascade="all, delete-orphan")
    batch_analysis_sessions = relationship("BatchAnalysisSession", back_populates="user", cascade="all, delete-orphan")
    custom_batch_analysis_sessions = relationship("CustomBatchAnalysisSession", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

