from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import date, datetime, timedelta
from typing import Optional, List
from statistics import mean
from pydantic import BaseModel

from app.core.database import get_db
from app.models.project import Project
from app.models.project_config import ProjectConfig
from app.models.test_case import TestCase
from app.schemas.project import (
    ProjectItem, ProjectListResponse, SummaryResponse, ProjectCreate, ProjectUpdate
)
from app.schemas.test_case import TestCaseItem, ProjectDetailResponse
from app.services.project_service import recalc_project_stats, compute_failure_rate, compute_analysis_progress

router = APIRouter()


# ========== 统一工程查询接口 ==========

class UnifiedProjectItem(BaseModel):
    """统一工程数据项，合并 Project 和 ProjectConfig 两表的所有字段"""
    project_id: Optional[int] = None      # Project 表的 id，不存在则为 None
    config_id: Optional[int] = None       # ProjectConfig 表的 id，不存在则为 None
    product_name: str
    version: str
    project_name: str
    # 以下字段来自 Project（不存在时为默认值）
    status: str = "lost"
    failure_reason: Optional[str] = None
    total_cases: int = 0
    total_failed_cases: int = 0
    analyzed_failed_cases: int = 0
    failure_rate: float = 0.0
    analysis_progress: float = 100.0
    last_report_at: Optional[datetime] = None
    # 以下字段两表都有，合并后取有效值
    owner: Optional[str] = None
    pl: Optional[str] = None


class UnifiedProjectListResponse(BaseModel):
    items: List[UnifiedProjectItem]
    total: int
    page: int
    size: int


@router.get("/unified-projects", response_model=UnifiedProjectListResponse)
def list_unified_projects(
    product_name: str = Query(...),
    version: str = Query(...),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    pl: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """统一工程查询：合并 Project 和 ProjectConfig 两表数据"""
    # 查询两表数据
    projects = db.query(Project).filter(
        Project.product_name == product_name,
        Project.version == version
    ).all()
    configs = db.query(ProjectConfig).filter(
        ProjectConfig.product_name == product_name,
        ProjectConfig.version == version
    ).all()

    # 以 project_name 为 key 建立索引
    project_map = {p.project_name: p for p in projects}
    config_map = {c.project_name: c for c in configs}

    # 合并：取两表 project_name 的并集
    all_names = set(project_map.keys()) | set(config_map.keys())

    items = []
    for name in all_names:
        p = project_map.get(name)
        c = config_map.get(name)

        # owner/pl 优先取 Project 的值，如果为空则取 ProjectConfig 的值
        owner_val = (p.owner if p and p.owner else (c.owner if c else None))
        pl_val = (p.pl if p and p.pl else (c.pl if c else None))

        item = UnifiedProjectItem(
            project_id=p.id if p else None,
            config_id=c.id if c else None,
            product_name=product_name,
            version=version,
            project_name=name,
            status=p.status if p else "lost",
            failure_reason=p.failure_reason if p else None,
            total_cases=p.total_cases if p else 0,
            total_failed_cases=p.total_failed_cases if p else 0,
            analyzed_failed_cases=p.analyzed_failed_cases if p else 0,
            failure_rate=compute_failure_rate(p) if p else 0.0,
            analysis_progress=compute_analysis_progress(p) if p else 100.0,
            last_report_at=p.last_report_at if p else None,
            owner=owner_val,
            pl=pl_val,
        )
        items.append(item)

    # 筛选
    if status:
        items = [i for i in items if i.status == status]
    if search:
        items = [i for i in items if search in i.project_name]
    if owner:
        items = [i for i in items if i.owner and owner in i.owner]
    if pl:
        items = [i for i in items if i.pl and pl in i.pl]

    # 按工程名排序
    items.sort(key=lambda x: x.project_name)

    # 分页
    total = len(items)
    start = (page - 1) * size
    end = start + size
    paged_items = items[start:end]

    return UnifiedProjectListResponse(items=paged_items, total=total, page=page, size=size)

def project_to_item(project: Project) -> ProjectItem:
    return ProjectItem(
        id=project.id,
        name=project.project_name,
        status=project.status,
        owner=project.owner,
        pl=project.pl,
        failure_reason=project.failure_reason,
        total_cases=project.total_cases,
        total_failed_cases=project.total_failed_cases,
        analyzed_failed_cases=project.analyzed_failed_cases,
        failure_rate=compute_failure_rate(project),
        analysis_progress=compute_analysis_progress(project),
        last_report_at=project.last_report_at
    )

@router.get("/products")
def get_products_and_versions(db: Session = Depends(get_db)):
    """获取所有产品名及其对应的版本列表（合并 Project 和 ProjectConfig）"""
    results = db.query(
        Project.product_name,
        Project.version
    ).distinct().order_by(Project.product_name, Project.version).all()

    config_results = db.query(
        ProjectConfig.product_name,
        ProjectConfig.version
    ).distinct().all()

    products_map = {}
    for product_name, version in list(results) + list(config_results):
        if product_name not in products_map:
            products_map[product_name] = []
        if version not in products_map[product_name]:
            products_map[product_name].append(version)

    products = [
        {"product_name": name, "versions": sorted(versions)}
        for name, versions in products_map.items()
    ]
    return {"products": products}

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

    failure_rates = [compute_failure_rate(p) for p in projects if p.total_cases > 0]
    avg_failure_rate = round(mean(failure_rates), 2) if failure_rates else 0.0

    progresses = [compute_analysis_progress(p) for p in projects if p.total_failed_cases > 0]
    avg_progress = round(mean(progresses), 2) if progresses else 100.0

    trend = []
    today = date.today()
    for i in range(4, -1, -1):
        day = today - timedelta(days=i)
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
    search: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    pl: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    # 查询 Project 表中的工程
    query = db.query(Project).filter(
        Project.product_name == product_name,
        Project.version == version
    )
    if status != "all":
        query = query.filter(Project.status == status)
    if search:
        query = query.filter(Project.project_name.contains(search))
    if owner:
        query = query.filter(Project.owner.contains(owner))
    if pl:
        query = query.filter(Project.pl.contains(pl))

    project_list = query.all()
    project_names_in_projects = {p.project_name for p in project_list}

    # 查询 ProjectConfig 中有但 Project 中没有的工程，合并进来
    config_query = db.query(ProjectConfig).filter(
        ProjectConfig.product_name == product_name,
        ProjectConfig.version == version
    )
    if project_names_in_projects:
        config_query = config_query.filter(
            ~ProjectConfig.project_name.in_(project_names_in_projects)
        )
    if search:
        config_query = config_query.filter(ProjectConfig.project_name.contains(search))
    if owner:
        config_query = config_query.filter(ProjectConfig.owner.contains(owner))
    if pl:
        config_query = config_query.filter(ProjectConfig.pl.contains(pl))
    # 仅当 status 筛选为 all 或 lost 时，才包含仅存在于配置中的工程（它们状态为 lost）
    if status == "all" or status == "lost":
        config_only = config_query.all()
    else:
        config_only = []

    # 将仅存在于 ProjectConfig 中的工程转为 ProjectItem 形式
    config_only_items = []
    for c in config_only:
        config_only_items.append(ProjectItem(
            id=-c.id,  # 用负数id区分来自ProjectConfig的记录，避免与Project id冲突
            name=c.project_name,
            status="lost",
            owner=c.owner,
            pl=c.pl,
            failure_reason=None,
            total_cases=0,
            total_failed_cases=0,
            analyzed_failed_cases=0,
            failure_rate=0.0,
            analysis_progress=100.0,
            last_report_at=None
        ))

    # 合并并按工程名排序
    all_items = [project_to_item(p) for p in project_list] + config_only_items
    all_items.sort(key=lambda x: x.name)

    # 手动分页
    total = len(all_items)
    start = (page - 1) * size
    end = start + size
    paged_items = all_items[start:end]

    return ProjectListResponse(items=paged_items, total=total, page=page, size=size)

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
            test_name=tc.test_name,
            status=tc.status,
            is_analyzed=tc.is_analyzed,
            failure_reason=tc.failure_reason,
            owner=tc.owner,
            pl=tc.pl,
            report_date=tc.report_date,
            last_report_at=tc.last_report_at,
            is_source_code_issue=tc.is_source_code_issue,
            dts_ticket=tc.dts_ticket,
            dts_link=None,   # 详情页链接可暂不生成，由前端编辑时再获取
            xml_summary=tc.xml_summary
        )
        for tc in test_cases
    ]

    base_item = project_to_item(project)
    return ProjectDetailResponse(
        **base_item.model_dump(),
        test_cases=case_items
    )

@router.post("/projects", response_model=ProjectItem, status_code=201)
def create_project(project_data: ProjectCreate, db: Session = Depends(get_db)):
    existing = db.query(Project).filter_by(
        product_name=project_data.product_name,
        version=project_data.version,
        project_name=project_data.project_name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Project already exists")

    project = Project(
        product_name=project_data.product_name,
        version=project_data.version,
        project_name=project_data.project_name,
        owner=project_data.owner,
        pl=project_data.pl,
        status="lost"
    )
    db.add(project)
    db.flush()
    # 同步创建或更新 ProjectConfig
    config = db.query(ProjectConfig).filter_by(
        product_name=project_data.product_name,
        version=project_data.version,
        project_name=project_data.project_name
    ).first()
    if config:
        if project_data.owner is not None:
            config.owner = project_data.owner
        if project_data.pl is not None:
            config.pl = project_data.pl
    else:
        config = ProjectConfig(
            product_name=project_data.product_name,
            version=project_data.version,
            project_name=project_data.project_name,
            owner=project_data.owner,
            pl=project_data.pl
        )
        db.add(config)
    db.commit()
    db.refresh(project)
    return project_to_item(project)

@router.patch("/projects/{project_id}")
def update_project(project_id: int, update_data: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(Project).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if update_data.owner is not None:
        project.owner = update_data.owner
    if update_data.pl is not None:
        project.pl = update_data.pl
    if update_data.failure_reason is not None:
        project.failure_reason = update_data.failure_reason
    # 同步更新 ProjectConfig 的 owner/pl
    config = db.query(ProjectConfig).filter_by(
        product_name=project.product_name,
        version=project.version,
        project_name=project.project_name
    ).first()
    if config:
        if update_data.owner is not None:
            config.owner = update_data.owner
        if update_data.pl is not None:
            config.pl = update_data.pl
    else:
        # ProjectConfig 不存在则自动创建
        config = ProjectConfig(
            product_name=project.product_name,
            version=project.version,
            project_name=project.project_name,
            owner=project.owner,
            pl=project.pl
        )
        db.add(config)
    db.commit()
    return {"message": "Project updated"}


@router.delete("/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """删除工程，同步删除对应的 ProjectConfig"""
    project = db.query(Project).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    # 同步删除对应的 ProjectConfig
    config = db.query(ProjectConfig).filter_by(
        product_name=project.product_name,
        version=project.version,
        project_name=project.project_name
    ).first()
    if config:
        db.delete(config)
    # 删除关联的测试用例
    db.query(TestCase).filter(TestCase.project_id == project_id).delete()
    db.delete(project)
    db.commit()
    return {"message": "Project deleted"}