from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReportCreate(BaseModel):
    test_project_name: str
    test_name: Optional[str] = None
    version: str
    group_id: str
    project_id: str
    record_id: str
    subrecord_id: str
    status: Optional[str] = None
    timestamp: Optional[datetime] = None
    log_url: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "test_project_name": "dhf_gmem_sdv",
                "version": "QingLuan V100R026C10",
                "group_id": "grp-001",
                "project_id": "proj-001",
                "record_id": "rec-456",
                "subrecord_id": "sub-001",
                "timestamp": "2026-04-09T10:15:00Z",
                "log_url": "https://example.com/logs/12345.zip"
            }
        }