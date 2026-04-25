from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Text, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import ArchiveBase

class ArchivedFailure(ArchiveBase):
    __tablename__ = "archived_failures"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(255), nullable=False)
    version = Column(String(255), nullable=False)
    project_name = Column(String(255), nullable=False)
    test_name = Column(String(255), nullable=False)
    failure_date = Column(Date, nullable=False, index=True)
    first_failure_date = Column(Date, nullable=False)
    consecutive_days = Column(Integer, default=1)
    consecutive_success_days = Column(Integer, default=0)  # 连续成功天数
    status = Column(String(20), nullable=False)
    is_analyzed = Column(Boolean, default=False)  # 分析状态
    failure_reason = Column(String, nullable=True)
    owner = Column(String(100), nullable=True)
    pl = Column(String(50), nullable=True)
    feature_name = Column(String(255), nullable=True)  # 所属特性
    is_probabilistic = Column(Boolean, default=False)  # 是否概率失败
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "product_name", "version", "project_name", "test_name", "failure_date",
            name="uq_archived_failure"
        ),
    )


class TestCaseExecutionHistory(ArchiveBase):
    """用例历史执行记录"""
    __tablename__ = "test_case_execution_history"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(255), nullable=False)
    version = Column(String(255), nullable=False)
    project_name = Column(String(255), nullable=False)
    test_name = Column(String(255), nullable=False)
    execution_date = Column(Date, nullable=False, index=True)
    status = Column(String(20), nullable=False)
    failure_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
