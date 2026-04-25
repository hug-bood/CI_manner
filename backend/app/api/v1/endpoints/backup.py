from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import json
import io
import shutil
import os
from datetime import datetime

from app.core.database import get_db, get_archive_db, engine, archive_engine
from app.models.project import Project
from app.models.test_case import TestCase
from app.models.archive import ArchivedFailure, TestCaseExecutionHistory

router = APIRouter(prefix="/backup", tags=["backup"])


class BackupInfo(BaseModel):
    product_name: str
    version: str
    project_count: int
    test_case_count: int
    archive_count: int


class BackupResponse(BaseModel):
    message: str
    data: dict


@router.get("/info")
def get_backup_info(
    product_name: Optional[str] = Query(None),
    version: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    archive_db: Session = Depends(get_archive_db)
):
    """获取版本数据统计信息"""
    query = db.query(Project)
    if product_name:
        query = query.filter(Project.product_name == product_name)
    if version:
        query = query.filter(Project.version == version)
    
    projects = query.all()
    project_ids = [p.id for p in projects]
    
    test_case_count = 0
    if project_ids:
        test_case_count = db.query(TestCase).filter(TestCase.project_id.in_(project_ids)).count()
    
    archive_query = archive_db.query(ArchivedFailure)
    if product_name:
        archive_query = archive_query.filter(ArchivedFailure.product_name == product_name)
    if version:
        archive_query = archive_query.filter(ArchivedFailure.version == version)
    archive_count = archive_query.count()
    
    return {
        "product_name": product_name,
        "version": version,
        "project_count": len(projects),
        "test_case_count": test_case_count,
        "archive_count": archive_count
    }


@router.post("/export")
def export_version_data(
    product_name: str = Query(...),
    version: str = Query(...),
    db: Session = Depends(get_db),
    archive_db: Session = Depends(get_archive_db)
):
    """导出指定版本的所有数据为JSON"""
    from fastapi.responses import StreamingResponse
    
    # 获取工程数据
    projects = db.query(Project).filter(
        Project.product_name == product_name,
        Project.version == version
    ).all()
    
    project_ids = [p.id for p in projects]
    
    # 获取用例数据
    test_cases = []
    if project_ids:
        test_cases = db.query(TestCase).filter(TestCase.project_id.in_(project_ids)).all()
    
    # 获取归档数据
    archives = archive_db.query(ArchivedFailure).filter(
        ArchivedFailure.product_name == product_name,
        ArchivedFailure.version == version
    ).all()
    
    # 获取执行历史
    histories = archive_db.query(TestCaseExecutionHistory).filter(
        TestCaseExecutionHistory.product_name == product_name,
        TestCaseExecutionHistory.version == version
    ).all()
    
    # 构建导出数据
    export_data = {
        "export_time": datetime.utcnow().isoformat(),
        "product_name": product_name,
        "version": version,
        "projects": [
            {
                "id": p.id,
                "project_name": p.project_name,
                "status": p.status,
                "owner": p.owner,
                "pl": p.pl,
                "failure_reason": p.failure_reason,
                "total_cases": p.total_cases,
                "total_failed_cases": p.total_failed_cases,
                "analyzed_failed_cases": p.analyzed_failed_cases,
                "last_report_at": p.last_report_at.isoformat() if p.last_report_at else None
            }
            for p in projects
        ],
        "test_cases": [
            {
                "id": tc.id,
                "project_id": tc.project_id,
                "test_name": tc.test_name,
                "status": tc.status,
                "is_analyzed": tc.is_analyzed,
                "failure_reason": tc.failure_reason,
                "owner": tc.owner,
                "pl": tc.pl,
                "is_source_code_issue": tc.is_source_code_issue,
                "dts_ticket": tc.dts_ticket,
                "last_report_at": tc.last_report_at.isoformat() if tc.last_report_at else None
            }
            for tc in test_cases
        ],
        "archives": [
            {
                "id": a.id,
                "project_name": a.project_name,
                "test_name": a.test_name,
                "failure_date": a.failure_date.isoformat() if a.failure_date else None,
                "first_failure_date": a.first_failure_date.isoformat() if a.first_failure_date else None,
                "consecutive_days": a.consecutive_days,
                "consecutive_success_days": a.consecutive_success_days,
                "status": a.status,
                "is_analyzed": a.is_analyzed,
                "failure_reason": a.failure_reason,
                "owner": a.owner,
                "pl": a.pl,
                "feature_name": a.feature_name,
                "is_probabilistic": a.is_probabilistic
            }
            for a in archives
        ],
        "execution_histories": [
            {
                "id": h.id,
                "project_name": h.project_name,
                "test_name": h.test_name,
                "execution_date": h.execution_date.isoformat() if h.execution_date else None,
                "status": h.status,
                "failure_reason": h.failure_reason
            }
            for h in histories
        ]
    }
    
    json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
    filename = f"backup_{product_name}_{version}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
    
    return StreamingResponse(
        io.BytesIO(json_str.encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/db-backup")
def backup_database_files():
    """备份数据库文件（物理备份）"""
    from fastapi.responses import FileResponse
    
    backup_dir = "./backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    results = []
    
    for db_file in ["./ci.db", "./ci_archive.db"]:
        if os.path.exists(db_file):
            backup_file = os.path.join(backup_dir, f"{os.path.basename(db_file)}.{timestamp}.bak")
            shutil.copy2(db_file, backup_file)
            results.append({"original": db_file, "backup": backup_file})
    
    return {"message": "数据库备份完成", "backups": results}
