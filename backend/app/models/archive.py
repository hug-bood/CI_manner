from sqlalchemy import Column, Integer, String, Date, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import ArchiveBase

class ArchivedFailure(ArchiveBase):
    __tablename__ = "archived_failures"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(255), nullable=False)
    version = Column(String(255), nullable=False)
    project_name = Column(String(255), nullable=False)
    # suite_name 已删除
    test_name = Column(String(255), nullable=False)
    failure_date = Column(Date, nullable=False, index=True)
    first_failure_date = Column(Date, nullable=False)
    consecutive_days = Column(Integer, default=1)
    status = Column(String(20), nullable=False)
    failure_reason = Column(String, nullable=True)
    owner = Column(String(100), nullable=True)
    pl = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "product_name", "version", "project_name", "test_name", "failure_date",
            name="uq_archived_failure"
        ),
    )