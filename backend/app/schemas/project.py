from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ProjectItem(BaseModel):
    id: int
    name: str
    status: str
    owner: Optional[str]
    pl: Optional[str]
    failure_reason: Optional[str] = None
    total_cases: int
    total_failed_cases: int
    analyzed_failed_cases: int
    failure_rate: float
    analysis_progress: float
    last_report_at: Optional[datetime]

    class Config:
        from_attributes = True

class ProjectListResponse(BaseModel):
    items: List[ProjectItem]
    total: int
    page: int
    size: int

class SummaryResponse(BaseModel):
    total_projects: int
    failed_projects: int
    total_failed_cases: int
    average_failure_rate: float
    average_analysis_progress: float
    analysis_trend: List[Optional[float]]

class ProjectUpdate(BaseModel):
    owner: Optional[str] = None
    pl: Optional[str] = None
    failure_reason: Optional[str] = None
    status: Optional[str] = None

class ProjectCreate(BaseModel):
    product_name: str
    version: str
    project_name: str
    owner: Optional[str] = None
    pl: Optional[str] = None