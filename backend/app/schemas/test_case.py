from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from app.schemas.project import ProjectItem

class TestCaseItem(BaseModel):
    id: int
    suite_name: str
    test_name: str
    status: str
    is_analyzed: bool
    failure_reason: Optional[str]
    owner: Optional[str]
    pl: Optional[str]
    report_date: Optional[date]
    last_report_at: Optional[datetime]

    class Config:
        from_attributes = True

class ProjectDetailResponse(ProjectItem):
    test_cases: List[TestCaseItem]

class StatusUpdateRequest(BaseModel):
    product_name: str
    version: str
    project_name: str
    suite_name: str
    test_name: str
    status: str  # pass, fail, lost, processing

class AnalyzeRequest(BaseModel):
    product_name: str
    version: str
    project_name: str
    suite_name: str
    test_name: str
    failure_reason: str

class TestCaseListResponse(BaseModel):
    items: List[TestCaseItem]
    total: int
    page: int
    size: int