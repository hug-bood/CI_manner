from sqlalchemy import Column, Integer, String, DateTime, Text, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(255), nullable=False)
    project_name = Column(String(255), nullable=False)
    version = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="lost")
    owner = Column(String(100), nullable=True)
    pl = Column(String(50), nullable=True)
    failure_reason = Column(Text, nullable=True)
    total_cases = Column(Integer, default=0)
    total_failed_cases = Column(Integer, default=0)
    analyzed_failed_cases = Column(Integer, default=0)
    last_report_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("product_name", "version", "project_name", name="uq_project"),
    )