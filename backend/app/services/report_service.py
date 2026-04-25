from sqlalchemy.orm import Session
from datetime import datetime
from fastapi.encoders import jsonable_encoder

from app.models.project import Project
from app.models.project_config import ProjectConfig
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
        # 同步创建 ProjectConfig（如果不存在）
        config = db.query(ProjectConfig).filter_by(
            product_name=product_name,
            version=report.version,
            project_name=report.test_project_name
        ).first()
        if not config:
            config = ProjectConfig(
                product_name=product_name,
                version=report.version,
                project_name=report.test_project_name
            )
            db.add(config)
    else:
        if project.status == "lost":
            project.status = "active"

    project.last_report_at = report.timestamp or datetime.utcnow()

    # 3. 处理 log_url（如果有）- 先处理日志以获取所有测试用例
    xml_summary = None
    log_path = None
    if report.log_url:
        try:
            # 使用临时ID下载日志
            temp_log_path = download_and_extract_zip(report.log_url, 0)
            log_path = temp_log_path
            # 解析 result_*.xml
            xml_summary = find_and_parse_result_xml(temp_log_path)
        except Exception as e:
            print(f"Failed to process log: {e}")

    # 4. 批量处理测试用例
    processed_test_cases = []
    
    if xml_summary and "details" in xml_summary:
        # 从XML中提取所有测试用例
        for test_detail in xml_summary["details"]:
            test_name = test_detail.get("name", "")
            is_pass = test_detail.get("pass", False)
            status = "pass" if is_pass else "fail"
            
            # 查找或创建用例记录
            test_case = db.query(TestCase).filter_by(
                project_id=project.id,
                test_name=test_name
            ).first()

            if not test_case:
                test_case = TestCase(
                    project_id=project.id,
                    test_name=test_name,
                    status=status
                )
                db.add(test_case)
                db.flush()
            else:
                test_case.status = status

            # 更新用例字段
            test_case.raw_data = jsonable_encoder(report.model_dump())
            test_case.last_report_at = report.timestamp or datetime.utcnow()
            if report.timestamp:
                test_case.report_date = report.timestamp.date()
            else:
                test_case.report_date = datetime.utcnow().date()
            
            if log_path:
                test_case.log_path = log_path
            if xml_summary:
                test_case.xml_summary = xml_summary
                
            processed_test_cases.append(test_case)
    elif report.test_name:
        # 如果没有XML详情，但提供了test_name，则按原逻辑处理单个用例
        test_case = db.query(TestCase).filter_by(
            project_id=project.id,
            test_name=report.test_name
        ).first()

        if not test_case:
            test_case = TestCase(
                project_id=project.id,
                test_name=report.test_name,
                status=report.status or "unknown"
            )
            db.add(test_case)
            db.flush()
        else:
            if report.status:
                test_case.status = report.status

        test_case.raw_data = jsonable_encoder(report.model_dump())
        test_case.last_report_at = report.timestamp or datetime.utcnow()
        if report.timestamp:
            test_case.report_date = report.timestamp.date()
        else:
            test_case.report_date = datetime.utcnow().date()
        
        if log_path:
            test_case.log_path = log_path
        if xml_summary:
            test_case.xml_summary = xml_summary
            
        processed_test_cases.append(test_case)

    db.commit()

    # 5. 重新计算工程统计
    recalc_project_stats(db, project.id)

    return project, processed_test_cases