from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import date

from app.core.database import get_archive_db
from app.models.archive import ArchivedFailure

router = APIRouter(prefix="/archive", tags=["archive"])

class ArchiveItem(BaseModel):
    id: int
    product_name: str
    version: str
    project_name: str
    suite_name: str
    test_name: str
    failure_date: date
    first_failure_date: date
    consecutive_days: int
    status: str
    failure_reason: Optional[str]
    owner: Optional[str]
    pl: Optional[str]

    class Config:
        from_attributes = True

class ArchiveListResponse(BaseModel):
    items: List[ArchiveItem]
    total: int
    page: int
    size: int

@router.get("/failures", response_model=ArchiveListResponse)
def list_archived_failures(
    product_name: Optional[str] = Query(None),
    version: Optional[str] = Query(None),
    project_name: Optional[str] = Query(None),
    suite_name: Optional[str] = Query(None),
    test_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    pl: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_archive_db)
):
    query = db.query(ArchivedFailure)
    if product_name:
        query = query.filter(ArchivedFailure.product_name == product_name)
    if version:
        query = query.filter(ArchivedFailure.version == version)
    if project_name:
        query = query.filter(ArchivedFailure.project_name.contains(project_name))
    if suite_name:
        query = query.filter(ArchivedFailure.suite_name.contains(suite_name))
    if test_name:
        query = query.filter(ArchivedFailure.test_name.contains(test_name))
    if status:
        query = query.filter(ArchivedFailure.status == status)
    if owner:
        query = query.filter(ArchivedFailure.owner.contains(owner))
    if pl:
        query = query.filter(ArchivedFailure.pl.contains(pl))

    total = query.count()
    items = query.order_by(ArchivedFailure.failure_date.desc()).offset((page - 1) * size).limit(size).all()
    return ArchiveListResponse(items=items, total=total, page=page, size=size)