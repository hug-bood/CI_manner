from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from pydantic import BaseModel
from datetime import date, timedelta

from app.core.database import get_archive_db, get_db
from app.models.archive import ArchivedFailure, TestCaseExecutionHistory
from app.models.product_version_config import ProductVersionConfig
from app.models.auth import User
from app.api.v1.endpoints.auth import require_cleanup

router = APIRouter(prefix="/archive", tags=["archive"])


class ArchiveItem(BaseModel):
    id: int
    product_name: str
    version: str
    project_name: str
    test_name: str
    failure_date: date
    first_failure_date: date
    consecutive_days: int
    consecutive_success_days: int = 0
    status: str
    is_analyzed: bool = False
    failure_reason: Optional[str] = None
    owner: Optional[str] = None
    pl: Optional[str] = None
    feature_name: Optional[str] = None
    is_probabilistic: bool = False

    class Config:
        from_attributes = True


class ArchiveListResponse(BaseModel):
    items: List[ArchiveItem]
    total: int
    page: int
    size: int


class ArchiveUpdate(BaseModel):
    is_analyzed: Optional[bool] = None
    failure_reason: Optional[str] = None
    is_probabilistic: Optional[bool] = None


class ExecutionHistoryItem(BaseModel):
    id: int
    product_name: str
    version: str
    project_name: str
    test_name: str
    execution_date: date
    status: str
    failure_reason: Optional[str] = None

    class Config:
        from_attributes = True


class ExecutionHistoryResponse(BaseModel):
    items: List[ExecutionHistoryItem]
    total: int


@router.get("/failures", response_model=ArchiveListResponse)
def list_archived_failures(
    product_name: Optional[str] = Query(None),
    version: Optional[str] = Query(None),
    project_name: Optional[str] = Query(None),
    test_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    pl: Optional[str] = Query(None),
    feature_name: Optional[str] = Query(None),
    is_analyzed: Optional[bool] = Query(None),
    is_probabilistic: Optional[bool] = Query(None),
    consecutive_success_days_min: Optional[int] = Query(None),
    consecutive_success_days_max: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_archive_db)
):
    """获取归档失败列表"""
    query = db.query(ArchivedFailure)
    if product_name:
        query = query.filter(ArchivedFailure.product_name == product_name)
    if version:
        query = query.filter(ArchivedFailure.version == version)
    if project_name:
        query = query.filter(ArchivedFailure.project_name.contains(project_name))
    if test_name:
        query = query.filter(ArchivedFailure.test_name.contains(test_name))
    if status:
        query = query.filter(ArchivedFailure.status == status)
    if owner:
        query = query.filter(ArchivedFailure.owner.contains(owner))
    if pl:
        query = query.filter(ArchivedFailure.pl.contains(pl))
    if feature_name:
        query = query.filter(ArchivedFailure.feature_name.contains(feature_name))
    if is_analyzed is not None:
        query = query.filter(ArchivedFailure.is_analyzed == is_analyzed)
    if is_probabilistic is not None:
        query = query.filter(ArchivedFailure.is_probabilistic == is_probabilistic)
    if consecutive_success_days_min is not None:
        query = query.filter(ArchivedFailure.consecutive_success_days >= consecutive_success_days_min)
    if consecutive_success_days_max is not None:
        query = query.filter(ArchivedFailure.consecutive_success_days <= consecutive_success_days_max)

    total = query.count()
    items = query.order_by(ArchivedFailure.failure_date.desc()).offset((page - 1) * size).limit(size).all()
    return ArchiveListResponse(items=items, total=total, page=page, size=size)


@router.get("/probabilistic-failures", response_model=ArchiveListResponse)
def list_probabilistic_failures(
    product_name: Optional[str] = Query(None),
    version: Optional[str] = Query(None),
    project_name: Optional[str] = Query(None),
    test_name: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    pl: Optional[str] = Query(None),
    feature_name: Optional[str] = Query(None),
    consecutive_success_days_min: Optional[int] = Query(None),
    consecutive_success_days_max: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_archive_db)
):
    """获取概率失败列表 - 只返回标记为概率失败的用例"""
    query = db.query(ArchivedFailure).filter(ArchivedFailure.is_probabilistic == True)
    if product_name:
        query = query.filter(ArchivedFailure.product_name == product_name)
    if version:
        query = query.filter(ArchivedFailure.version == version)
    if project_name:
        query = query.filter(ArchivedFailure.project_name.contains(project_name))
    if test_name:
        query = query.filter(ArchivedFailure.test_name.contains(test_name))
    if owner:
        query = query.filter(ArchivedFailure.owner.contains(owner))
    if pl:
        query = query.filter(ArchivedFailure.pl.contains(pl))
    if feature_name:
        query = query.filter(ArchivedFailure.feature_name.contains(feature_name))
    if consecutive_success_days_min is not None:
        query = query.filter(ArchivedFailure.consecutive_success_days >= consecutive_success_days_min)
    if consecutive_success_days_max is not None:
        query = query.filter(ArchivedFailure.consecutive_success_days <= consecutive_success_days_max)

    total = query.count()
    items = query.order_by(ArchivedFailure.failure_date.desc()).offset((page - 1) * size).limit(size).all()
    return ArchiveListResponse(items=items, total=total, page=page, size=size)


@router.patch("/failures/{failure_id}")
def update_archived_failure(failure_id: int, data: ArchiveUpdate, db: Session = Depends(get_archive_db)):
    """更新归档记录（标记分析状态、概率失败等）"""
    failure = db.query(ArchivedFailure).get(failure_id)
    if not failure:
        raise HTTPException(status_code=404, detail="归档记录不存在")
    if data.is_analyzed is not None:
        failure.is_analyzed = data.is_analyzed
    if data.failure_reason is not None:
        failure.failure_reason = data.failure_reason
    if data.is_probabilistic is not None:
        failure.is_probabilistic = data.is_probabilistic
    db.commit()
    return {"message": "归档记录已更新"}


@router.delete("/failures/cleanup")
def cleanup_archived_failures(
    product_name: str = Query(...),
    version: str = Query(...),
    cleanup_user: User = Depends(require_cleanup),
    archive_db: Session = Depends(get_archive_db),
    db: Session = Depends(get_db)
):
    """人工清理归档记录 - 需要清理权限
    使用产品版本级别的 retention_days 配置：
    清理条件：已分析 且 连续成功天数 >= 该产品版本的 retention_days
    未配置则默认 30 天
    """
    # 读取该产品版本的 retention_days 配置
    config = db.query(ProductVersionConfig).filter(
        ProductVersionConfig.product_name == product_name,
        ProductVersionConfig.version == version
    ).first()
    retention_days = config.retention_days if config else 30

    # 查找可清理的记录：已分析且连续成功天数 >= retention_days
    to_cleanup = archive_db.query(ArchivedFailure).filter(
        ArchivedFailure.product_name == product_name,
        ArchivedFailure.version == version,
        ArchivedFailure.is_analyzed == True,
        ArchivedFailure.consecutive_success_days > 0,
        ArchivedFailure.consecutive_success_days >= retention_days
    ).all()

    count = len(to_cleanup)
    for item in to_cleanup:
        archive_db.delete(item)
    archive_db.commit()

    return {"message": f"已清理 {count} 条归档记录（保留天数: {retention_days}天）", "count": count, "retention_days": retention_days}


@router.get("/execution-history", response_model=ExecutionHistoryResponse)
def get_execution_history(
    product_name: str = Query(...),
    version: str = Query(...),
    project_name: Optional[str] = Query(None),
    test_name: str = Query(...),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_archive_db)
):
    """获取用例历史执行记录"""
    query = db.query(TestCaseExecutionHistory).filter(
        TestCaseExecutionHistory.product_name == product_name,
        TestCaseExecutionHistory.version == version,
        TestCaseExecutionHistory.test_name == test_name
    )
    if project_name:
        query = query.filter(TestCaseExecutionHistory.project_name == project_name)
    
    total = query.count()
    items = query.order_by(TestCaseExecutionHistory.execution_date.desc()).offset((page - 1) * size).limit(size).all()
    return ExecutionHistoryResponse(items=items, total=total)
