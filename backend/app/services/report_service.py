from sqlalchemy.orm import Session
from datetime import datetime
from fastapi.encoders import jsonable_encoder

from app.models.project import Project
from app.models.test_case import TestCase
from app.schemas.report import ReportCreate
from app.services.project_service import recalc_project_stats
from app.services.log_service import download_and_extract_zip
from app.services.xml_parser import find_and_parse_result_xml

def parse_version(version_str: str):
    """从完整版本字符串提取产品名和版本号"""
    parts = version_str.split(" ", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    else:
        return version_str, ""

def process_report(db: Session, report: ReportCreate):
    # 1. 解析产品名和版本
    product_name, version_only = parse_version(report.version)

    # 2. 查找或创建工程
    project = db.query(Project).filter_by(
        product_name=product_name,
        version=report.version,
        project_name=report.test_project_name
    ).first()

    if not project:
        project = Project(
            product_name=product_name,
            version=report.version,
            project_name=report.test_project_name,
            status="active"
        )
        db.add(project)
        db.flush()  # 获取 id
    else:
        if project.status == "lost":
            project.status = "active"

    project.last_report_at = report.timestamp or datetime.utcnow()

    # 3. 查找或创建用例记录
    test_case = db.query(TestCase).filter_by(
        project_id=project.id,
        test_name=report.test_name
    ).first()

    if not test_case:
        test_case = TestCase(
            project_id=project.id,
            test_name=report.test_name,
            status=report.status          # 创建时直接赋予 status
        )
        db.add(test_case)
        db.flush()  # 获取 test_case.id
    else:
        test_case.status = report.status

    # 4. 更新其他用例字段
    test_case.raw_data = jsonable_encoder(report.model_dump())
    test_case.last_report_at = report.timestamp or datetime.utcnow()
    if report.timestamp:
        test_case.report_date = report.timestamp.date()
    else:
        test_case.report_date = datetime.utcnow().date()

    # 5. 处理 log_url（如果有）
    if report.log_url:
        try:
            log_path = download_and_extract_zip(report.log_url, test_case.id)
            test_case.log_path = log_path
            # 解析 result_*.xml
            summary = find_and_parse_result_xml(log_path)
            if summary:
                test_case.xml_summary = summary
        except Exception as e:
            print(f"Failed to process log for test_case {test_case.id}: {e}")

    db.commit()

    # 6. 重新计算工程统计
    recalc_project_stats(db, project.id)

    return project, test_case