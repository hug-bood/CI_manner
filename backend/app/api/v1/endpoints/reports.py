from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.report import ReportCreate
from app.services.report_service import process_report
import traceback

router = APIRouter()

@router.post("/reports", status_code=status.HTTP_201_CREATED)
def create_report(report: ReportCreate, db: Session = Depends(get_db)):
    """接收 CI 上报数据"""
    try:
        project, test_case = process_report(db, report)
        return {"message": "Report processed", "project_id": project.id, "test_case_id": test_case.id}
    except Exception as e:
        # 打印完整堆栈到控制台，便于调试
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))