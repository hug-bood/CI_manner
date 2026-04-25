from sqlalchemy import Column, Integer, String, Boolean, Text, Date, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    test_name = Column(String(255), nullable=False)
    record_id = Column(String(255), nullable=True)          # 用于区分不同批次的上报
    status = Column(String(20), nullable=False)
    is_analyzed = Column(Boolean, default=False)
    failure_reason = Column(Text, nullable=True)
    owner = Column(String(100), nullable=True)
    pl = Column(String(50), nullable=True)
    report_date = Column(Date, nullable=True)
    raw_data = Column(JSON, nullable=True)
    last_report_at = Column(DateTime, nullable=True)
    is_source_code_issue = Column(Boolean, default=False)
    dts_ticket = Column(String(100), nullable=True)
    log_path = Column(String(500), nullable=True)
    xml_summary = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())