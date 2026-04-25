from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base

class Feature(Base):
    """特性模型：支持特性 -> 工程 -> 用例的层级结构"""
    __tablename__ = "features"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(255), nullable=False)
    version = Column(String(255), nullable=False)
    feature_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class ProjectFeatureMapping(Base):
    """工程-特性映射表：一个工程可以属于多个特性"""
    __tablename__ = "project_feature_mappings"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, nullable=False, index=True)
    feature_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
