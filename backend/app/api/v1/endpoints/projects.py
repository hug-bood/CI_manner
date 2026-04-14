from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date, timedelta
from typing import Optional, List
from statistics import mean

from app.core.database import get_db
from app.models.project import Project
from app.models.test_case import TestCase
from app.schemas.project import ProjectItem, ProjectListResponse, SummaryResponse
from app.schemas.test_case import ProjectDetailResponse, TestCaseItem
from app.services.project_service import compute_failure_rate, compute_analysis_progress
from app.schemas.project import ProjectUpdate

router = APIRouter()

def project_to_item(project: Project) -> ProjectItem:
    return ProjectItem(
        id=project.id,
        name=project.project_name,
        status=project.status,
        owner=project.owner,
        pl=project.pl,
        total_cases=project.total_cases,
        total_failed_cases=project.total_failed_cases,
        analyzed_failed_cases=project.analyzed_failed_cases,
        failure_rate=compute_failure_rate(project),
        analysis_progress=compute_analysis_progress(project),
        last_report_at=project.last_report_at
    )

@router.get("/products/{product_name}/versions/{version}/summary", response_model=SummaryResponse)
def get_summary(
    product_name: str,
    version: str,
    db: Session = Depends(get_db)
):
    """获取工程汇总仪表盘数据"""
    projects = db.query(Project).filter(
        Project.product_name == product_name,
        Project.version == version
    ).all()

    total = len(projects)
    failed = sum(1 for p in projects if p.status == "failure")
    total_failed_cases = sum(p.total_failed_cases for p in projects)

    # 平均失败率
    failure_rates = [compute_failure_rate(p) for p in projects if p.total_cases > 0]
    avg_failure_rate = round(mean(failure_rates), 2) if failure_rates else 0.0

    # 平均分析进展
    progresses = [compute_analysis_progress(p) for p in projects if p.total_failed_cases > 0]
    avg_progress = round(mean(progresses), 2) if progresses else 100.0

    # 近5天趋势：按 report_date 分组计算每天的平均分析进展
    trend = []
    today = date.today()
    for i in range(4, -1, -1):  # 从4天前到今天
        day = today - timedelta(days=i)
        # 获取当天有上报的工程（通过 last_report_at 判断）
        day_projects = [p for p in projects if p.last_report_at and p.last_report_at.date() == day]
        day_progresses = [compute_analysis_progress(p) for p in day_projects if p.total_failed_cases > 0]
        trend.append(round(mean(day_progresses), 2) if day_progresses else None)

    return SummaryResponse(
        total_projects=total,
        failed_projects=failed,
        total_failed_cases=total_failed_cases,
        average_failure_rate=avg_failure_rate,
        average_analysis_progress=avg_progress,
        analysis_trend=trend
    )


@router.get("/products/{product_name}/versions/{version}/projects", response_model=ProjectListResponse)
def list_projects(
        product_name: str,
        version: str,
        page: int = Query(1, ge=1),
        size: int = Query(20, ge=1, le=100),
        status: Optional[str] = Query("all", regex="^(all|success|failure|lost)$"),
        search: Optional[str] = Query(None, description="工程名模糊搜索"),
        owner: Optional[str] = Query(None, description="责任人模糊搜索"),
        pl: Optional[str] = Query(None, description="PL模糊搜索"),
        db: Session = Depends(get_db)
):
    query = db.query(Project).filter(
        Project.product_name == product_name,
        Project.version == version
    )

    # 状态筛选
    if status != "all":
        query = query.filter(Project.status == status)

    # 工程名模糊搜索
    if search:
        query = query.filter(Project.project_name.contains(search))

    # 责任人模糊搜索
    if owner:
        query = query.filter(Project.owner.contains(owner))

    # PL模糊搜索
    if pl:
        query = query.filter(Project.pl.contains(pl))

    total = query.count()
    projects = query.offset((page - 1) * size).limit(size).all()

    items = [project_to_item(p) for p in projects]
    return ProjectListResponse(items=items, total=total, page=page, size=size)

@router.get("/projects/{project_id}", response_model=ProjectDetailResponse)
def get_project_detail(project_id: int, db: Session = Depends(get_db)):
    """获取工程详情（含用例列表）"""
    project = db.query(Project).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    test_cases = db.query(TestCase).filter(TestCase.project_id == project_id).all()
    case_items = [
        TestCaseItem(
            id=tc.id,
            suite_name=tc.suite_name,
            test_name=tc.test_name,
            status=tc.status,
            is_analyzed=tc.is_analyzed,
            failure_reason=tc.failure_reason,
            owner=tc.owner,
            pl=tc.pl,
            report_date=tc.report_date,
            last_report_at=tc.last_report_at
        )
        for tc in test_cases
    ]

    base_item = project_to_item(project)
    return ProjectDetailResponse(
        **base_item.model_dump(),
        test_cases=case_items
    )


@router.get("/products")
def get_products_and_versions(db: Session = Depends(get_db)):
    """获取所有产品名及其对应的版本列表"""
    # 查询所有不同的产品名和版本组合
    results = db.query(
        Project.product_name,
        Project.version
    ).distinct().order_by(Project.product_name, Project.version).all()

    # 按产品名分组
    products_map = {}
    for product_name, version in results:
        if product_name not in products_map:
            products_map[product_name] = []
        if version not in products_map[product_name]:
            products_map[product_name].append(version)

    # 转换为列表格式
    products = [
        {"product_name": name, "versions": versions}
        for name, versions in products_map.items()
    ]

    return {"products": products}

@router.patch("/projects/{project_id}")
def update_project(project_id: int, update_data: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(Project).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if update_data.owner is not None:
        project.owner = update_data.owner
    if update_data.pl is not None:
        project.pl = update_data.pl
    db.commit()
    return {"message": "Project updated"}