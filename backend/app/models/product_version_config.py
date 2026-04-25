from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base

class ProductVersionConfig(Base):
    """产品版本级别配置：保留天数等"""
    __tablename__ = "product_version_configs"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(255), nullable=False)
    version = Column(String(255), nullable=False)
    retention_days = Column(Integer, default=30)  # 已修复历史用例保留天数
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("product_name", "version", name="uq_product_version_config"),
    )
