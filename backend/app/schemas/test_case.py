from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

# 导入工程基础模型用于组合
from app.schemas.project import ProjectItem

class TestCaseItem(BaseModel):
    id: int
    test_name: str
    status: str
    is_analyzed: bool
    failure_reason: Optional[str]
    owner: Optional[str]
    pl: Optional[str]
    report_date: Optional[date]
    last_report_at: Optional[datetime]
    is_source_code_issue: bool = False
    dts_ticket: Optional[str] = None
    dts_link: Optional[str] = None

    class Config:
        from_attributes = True

class TestCaseListResponse(BaseModel):
    items: List[TestCaseItem]
    total: int
    page: int
    size: int

class StatusUpdateRequest(BaseModel):
    product_name: str
    version: str
    project_name: str
    test_name: str
    status: str  # pass, fail, lost, processing

class AnalyzeRequest(BaseModel):
    product_name: str
    version: str
    project_name: str
    test_name: str
    failure_reason: str

class ProjectDetailResponse(ProjectItem):
    test_cases: List[TestCaseItem]