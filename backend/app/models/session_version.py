"""
会话版本表：存储某次报告/图表的快照
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class AnalysisSessionVersion(Base):
    __tablename__ = "analysis_session_versions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    version_no = Column(Integer, nullable=False)
    summary = Column(String(255), nullable=True)
    report_text = Column(Text, nullable=True)
    report_html_charts = Column(Text, nullable=True)
    report_charts_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    session = relationship("AnalysisSession", back_populates="versions")

    def __repr__(self):
        return f"<AnalysisSessionVersion(id={self.id}, session_id={self.session_id}, version_no={self.version_no})>"










