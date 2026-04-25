from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    """用户模型：支持管理员鉴权"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False, default="")
    is_admin = Column(Boolean, default=False)
    can_cleanup = Column(Boolean, default=False)  # 人工清理权限
    created_at = Column(DateTime, server_default=func.now())
