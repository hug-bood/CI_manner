from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    """用户模型：支持管理员鉴权"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False, default="")
    is_admin = Column(Boolean, default=False)
    can_cleanup = Column(Boolean, default=False)
    last_product = Column(String(255), nullable=True)
    last_version = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class UserToken(Base):
    """用户Token持久化表"""
    __tablename__ = "user_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(64), nullable=False, unique=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    expire_time = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
