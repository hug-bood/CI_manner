from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.project import Project
from app.models.test_case import TestCase
from app.services.project_service import recalc_project_stats
from app.schemas.test_case import TestCaseItem, TestCaseListResponse

router = APIRouter()

class TestCaseUpdate(BaseModel):
    owner: Optional[str] = None
    pl: Optional[str] = None
    status: Optional[str] = None
    failure_reason: Optional[str] = None
    is_analyzed: Optional[bool] = None
    is_source_code_issue: Optional[bool] = None
    is_probabilistic: Optional[bool] = None
    dts_ticket: Optional[str] = None

class AnalyzeRequest(BaseModel):
    product_name: str
    version: str
    project_name: str
    test_name: str
    failure_reason: str

def locate_project_and_case(db: Session, product_name: str, version: str, project_name: str, test_name: str):
    project = db.query(Project).filter_by(
        product_name=product_name,
        version=version,
        project_name=project_name
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    test_case = db.query(TestCase).filter_by(
        project_id=project.id,
        test_name=test_name
    ).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    return project, test_case

def generate_dts_link(ticket: str) -> str:
    return f"https://dts.company.com/ticket/{ticket}"

@router.patch("/test-cases/{test_case_id}")
def update_test_case(test_case_id: int, update_data: TestCaseUpdate, db: Session = Depends(get_db)):
    test_case = db.query(TestCase).get(test_case_id)
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    if update_data.owner is not None:
        test_case.owner = update_data.owner
    if update_data.pl is not None:
        test_case.pl = update_data.pl
    if update_data.status is not None:
        test_case.status = update_data.status
        if update_data.status in ("processing", "pass"):
            test_case.is_analyzed = True
    if update_data.failure_reason is not None:
        test_case.failure_reason = update_data.failure_reason
    if update_data.is_analyzed is not None:
        test_case.is_analyzed = update_data.is_analyzed
    if update_data.is_source_code_issue is not None:
        test_case.is_source_code_issue = update_data.is_source_code_issue
    if update_data.is_probabilistic is not None:
        test_case.is_probabilistic = update_data.is_probabilistic
    if update_data.dts_ticket is not None:
        test_case.dts_ticket = update_data.dts_ticket

    db.commit()
    recalc_project_stats(db, test_case.project_id)
    return {"message": "Test case updated"}

@router.post("/test-cases/analyze")
def analyze_test_case(request: AnalyzeRequest, db: Session = Depends(get_db)):
    project, test_case = locate_project_and_case(
        db, request.product_name, request.version, request.project_name,
        request.test_name
    )
    test_case.failure_reason = request.failure_reason
    test_case.is_analyzed = True
    db.commit()
    recalc_project_stats(db, project.id)
    return {"message": "Analysis recorded"}

@router.get("/test-cases", response_model=TestCaseListResponse)
def list_test_cases(
    project_id: Optional[int] = Query(None),
    test_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    pl: Optional[str] = Query(None),
    is_analyzed: Optional[bool] = Query(None),
    is_source_code_issue: Optional[bool] = Query(None),
    failed_only: bool = Query(False),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(TestCase)
    if project_id:
        query = query.filter(TestCase.project_id == project_id)
    if test_name:
        query = query.filter(TestCase.test_name.contains(test_name))
    if status:
        query = query.filter(TestCase.status == status)
    if owner:
        query = query.filter(TestCase.owner.contains(owner))
    if pl:
        query = query.filter(TestCase.pl.contains(pl))
    if is_analyzed is not None:
        query = query.filter(TestCase.is_analyzed == is_analyzed)
    if is_source_code_issue is not None:
        query = query.filter(TestCase.is_source_code_issue == is_source_code_issue)
    if failed_only:
        query = query.filter(TestCase.status.in_(['fail', 'lost', 'processing']))

    total = query.count()
    test_cases = query.offset((page - 1) * size).limit(size).all()

    items = []
    for tc in test_cases:
        dts_link = generate_dts_link(tc.dts_ticket) if tc.dts_ticket else None
        items.append(TestCaseItem(
            id=tc.id,
            test_name=tc.test_name,
            status=tc.status,
            is_analyzed=tc.is_analyzed,
            failure_reason=tc.failure_reason,
            owner=tc.owner,
            pl=tc.pl,
            report_date=tc.report_date,
            last_report_at=tc.last_report_at,
            is_source_code_issue=tc.is_source_code_issue,
            is_probabilistic=tc.is_probabilistic,
            dts_ticket=tc.dts_ticket,
            dts_link=dts_link,
            xml_summary=tc.xml_summary
        ))
    return TestCaseListResponse(items=items, total=total, page=page, size=size)