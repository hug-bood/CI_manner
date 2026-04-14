from sqlalchemy.orm import Session
from datetime import datetime
from app.models.project import Project
from app.models.test_case import TestCase
from app.schemas.report import ReportCreate
from app.services.project_service import recalc_project_stats
from fastapi.encoders import jsonable_encoder

def parse_version(version_str: str):
    """从完整版本字符串提取产品名和版本号"""
    parts = version_str.split(" ", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    else:
        return version_str, ""  # fallback

def process_report(db: Session, report: ReportCreate):
    # 1. 解析产品名和版本
    product_name, version_only = parse_version(report.version)

    # 2. 查找或创建工程
    project = db.query(Project).filter_by(
        product_name=product_name,
        version=report.version,   # 存储完整字符串
        project_name=report.test_project_name
    ).first()

    if not project:
        project = Project(
            product_name=product_name,
            version=report.version,
            project_name=report.test_project_name,
            status="active"  # 初始状态
        )
        db.add(project)
        db.flush()  # 获取 id
    else:
        # 如果当前是 lost，上报后改为 active
        if project.status == "lost":
            project.status = "active"

    project.last_report_at = report.timestamp or datetime.utcnow()

    # 3. 查找或创建用例记录
    test_case = db.query(TestCase).filter_by(
        project_id=project.id,
        suite_name=report.test_suite_name,
        test_name=report.test_name
    ).first()

    if not test_case:
        test_case = TestCase(
            project_id=project.id,
            suite_name=report.test_suite_name,
            test_name=report.test_name
        )
        db.add(test_case)

    # 4. 更新用例字段
    test_case.status = report.status
    test_case.raw_data = jsonable_encoder(report.model_dump())
    test_case.last_report_at = report.timestamp or datetime.utcnow()
    if report.timestamp:
        test_case.report_date = report.timestamp.date()
    else:
        test_case.report_date = datetime.utcnow().date()

    db.commit()

    # 5. 重新计算工程统计
    recalc_project_stats(db, project.id)

    return project, test_case