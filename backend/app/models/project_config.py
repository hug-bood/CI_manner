from sqlalchemy import Column, Integer, String, DateTime, Text, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base

class ProjectConfig(Base):
    """工程配置模型：保留周期、工程/PL/责任人表格配置"""
    __tablename__ = "project_configs"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(255), nullable=False)
    version = Column(String(255), nullable=False)
    project_name = Column(String(255), nullable=False)
    pl = Column(String(50), nullable=True)
    owner = Column(String(100), nullable=True)
    retention_days = Column(Integer, default=30)  # 保留周期（天）
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("product_name", "version", "project_name", name="uq_project_config"),
    )
