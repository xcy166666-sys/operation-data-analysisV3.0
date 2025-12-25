"""
功能模块模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class FunctionModule(Base):
    """功能模块表"""
    __tablename__ = "function_modules"
    
    id = Column(Integer, primary_key=True, index=True)
    function_key = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    route_path = Column(String(200))
    icon = Column(String(50))
    category = Column(String(50), default='operation')
    is_enabled = Column(Boolean, default=True, nullable=False, index=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<FunctionModule(id={self.id}, function_key='{self.function_key}', name='{self.name}')>"

