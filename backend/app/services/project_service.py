from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from app.models.project import Project
from app.models.test_case import TestCase

FAILURE_STATUSES = ["fail", "lost", "processing"]

def recalc_project_stats(db: Session, project_id: int):
    project = db.query(Project).get(project_id)
    if not project:
        return

    total = db.query(func.count(TestCase.id)).filter(TestCase.project_id == project_id).scalar()
    failed = db.query(func.count(TestCase.id)).filter(
        TestCase.project_id == project_id,
        TestCase.status.in_(['fail', 'lost', 'processing'])
    ).scalar()
    analyzed = db.query(func.count(TestCase.id)).filter(
        TestCase.project_id == project_id,
        TestCase.status.in_(['fail', 'lost', 'processing']),
        TestCase.is_analyzed == True
    ).scalar()

    project.total_cases = total or 0
    project.total_failed_cases = failed or 0
    project.analyzed_failed_cases = analyzed or 0

    if project.total_failed_cases == 0:
        # 没有失败用例，状态为成功
        project.status = 'success'
    elif project.analyzed_failed_cases >= project.total_failed_cases:
        # 所有失败用例都已分析（已修复），状态自动置为成功
        project.status = 'success'
    elif project.status in ('success', 'active'):
        # 有未分析的失败用例，状态应为失败
        project.status = 'failure'
    # 其他情况（如当前已是 failure/lost）保持不变

    db.commit()

def compute_failure_rate(project: Project) -> float:
    if project.total_cases == 0:
        return 0.0
    return round((project.total_failed_cases / project.total_cases) * 100, 2)

def compute_analysis_progress(project: Project) -> float:
    if project.total_failed_cases == 0:
        return 100.0
    return round((project.analyzed_failed_cases / project.total_failed_cases) * 100, 2)