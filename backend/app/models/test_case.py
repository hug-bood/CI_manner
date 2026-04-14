from sqlalchemy import Column, Integer, String, Boolean, Text, Date, JSON, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base

class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    suite_name = Column(String(255), nullable=False)
    test_name = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False)
    is_analyzed = Column(Boolean, default=False)
    failure_reason = Column(Text, nullable=True)
    owner = Column(String(100), nullable=True)
    pl = Column(String(50), nullable=True)
    report_date = Column(Date, nullable=True)
    raw_data = Column(JSON, nullable=True)
    last_report_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("project_id", "suite_name", "test_name", name="uq_testcase"),
    )