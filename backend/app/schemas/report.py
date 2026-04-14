from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReportCreate(BaseModel):
    test_project_name: str
    test_suite_name: str
    test_name: str
    version: str
    group_id: Optional[str] = None
    project_id: Optional[str] = None
    record_id: Optional[str] = None
    subrecord_id: Optional[str] = None
    status: str  # pass, fail, lost
    timestamp: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "test_project_name": "dhf_gmem_sdv",
                "test_suite_name": "SUit_Gmem_API_TEST",
                "test_name": "Test_Gmem_API_001",
                "version": "QingLuan V100R026C10",
                "group_id": "group-001",
                "project_id": "proj-123",
                "record_id": "rec-456",
                "subrecord_id": "sub-789",
                "status": "fail",
                "timestamp": "2026-04-09T10:15:00Z"
            }
        }