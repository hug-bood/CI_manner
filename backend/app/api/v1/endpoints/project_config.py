from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import csv
import io

from app.core.database import get_db
from app.models.project_config import ProjectConfig
from app.models.project import Project

router = APIRouter(prefix="/project-configs", tags=["project_configs"])


class ProjectConfigItem(BaseModel):
    id: int
    product_name: str
    version: str
    project_name: str
    pl: Optional[str] = None
    owner: Optional[str] = None
    retention_days: int = 30

    class Config:
        from_attributes = True


class ProjectConfigCreate(BaseModel):
    product_name: str
    version: str
    project_name: str
    pl: Optional[str] = None
    owner: Optional[str] = None
    retention_days: int = 30


class ProjectConfigUpdate(BaseModel):
    pl: Optional[str] = None
    owner: Optional[str] = None
    retention_days: Optional[int] = None
    status: Optional[str] = None


class ProjectConfigListResponse(BaseModel):
    items: List[ProjectConfigItem]
    total: int
    page: int
    size: int


@router.get("", response_model=ProjectConfigListResponse)
def list_project_configs(
    product_name: Optional[str] = Query(None),
    version: Optional[str] = Query(None),
    project_name: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取工程配置列表，合并 Project 中有但 ProjectConfig 中没有的工程"""
    # 查询 ProjectConfig 表
    query = db.query(ProjectConfig)
    if product_name:
        query = query.filter(ProjectConfig.product_name == product_name)
    if version:
        query = query.filter(ProjectConfig.version == version)
    if project_name:
        query = query.filter(ProjectConfig.project_name.contains(project_name))

    config_list = query.all()
    config_names = {c.project_name for c in config_list}

    # 查询 Project 中有但 ProjectConfig 中没有的工程，合并进来
    project_query = db.query(Project)
    if config_names:
        project_query = project_query.filter(
            ~Project.project_name.in_(config_names)
        )
    if product_name:
        project_query = project_query.filter(Project.product_name == product_name)
    if version:
        project_query = project_query.filter(Project.version == version)
    if project_name:
        project_query = project_query.filter(Project.project_name.contains(project_name))

    project_only = project_query.all()

    # 将仅存在于 Project 中的工程转为 ProjectConfigItem 形式
    project_only_items = []
    for p in project_only:
        project_only_items.append(ProjectConfigItem(
            id=-p.id,  # 用负数id区分来自Project的记录
            product_name=p.product_name,
            version=p.version,
            project_name=p.project_name,
            pl=p.pl,
            owner=p.owner,
            retention_days=30
        ))

    # 合并并按工程名排序
    all_items = [ProjectConfigItem(
        id=c.id,
        product_name=c.product_name,
        version=c.version,
        project_name=c.project_name,
        pl=c.pl,
        owner=c.owner,
        retention_days=c.retention_days
    ) for c in config_list] + project_only_items
    all_items.sort(key=lambda x: x.project_name)

    # 手动分页
    total = len(all_items)
    start = (page - 1) * size
    end = start + size
    paged_items = all_items[start:end]

    return ProjectConfigListResponse(items=paged_items, total=total, page=page, size=size)


@router.post("", response_model=ProjectConfigItem, status_code=201)
def create_project_config(data: ProjectConfigCreate, db: Session = Depends(get_db)):
    """创建工程配置"""
    existing = db.query(ProjectConfig).filter_by(
        product_name=data.product_name,
        version=data.version,
        project_name=data.project_name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="配置已存在")
    config = ProjectConfig(**data.model_dump())
    db.add(config)
    db.flush()
    # 确保 Project 存在（不覆盖 owner/pl）
    project = db.query(Project).filter_by(
        product_name=data.product_name,
        version=data.version,
        project_name=data.project_name
    ).first()
    if not project:
        project = Project(
            product_name=data.product_name,
            version=data.version,
            project_name=data.project_name,
            status="lost"
        )
        db.add(project)
    db.commit()
    db.refresh(config)
    return config


@router.patch("/{config_id}", response_model=ProjectConfigItem)
def update_project_config(config_id: int, data: ProjectConfigUpdate, db: Session = Depends(get_db)):
    """更新工程配置"""
    config = db.query(ProjectConfig).get(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    if data.pl is not None:
        config.pl = data.pl
    if data.owner is not None:
        config.owner = data.owner
    if data.retention_days is not None:
        config.retention_days = data.retention_days
    # status 仍需同步到 Project（工程配置可设置进展状态）
    project = db.query(Project).filter_by(
        product_name=config.product_name,
        version=config.version,
        project_name=config.project_name
    ).first()
    if project:
        if data.status is not None:
            if data.status not in ('success', 'failure', 'lost'):
                raise HTTPException(status_code=400, detail="Invalid status value, must be success/failure/lost")
            project.status = data.status
    else:
        if data.status is not None and data.status in ('success', 'failure', 'lost'):
            project = Project(
                product_name=config.product_name,
                version=config.version,
                project_name=config.project_name,
                status=data.status
            )
            db.add(project)
    db.commit()
    db.refresh(config)
    return config


@router.delete("/{config_id}")
def delete_project_config(config_id: int, db: Session = Depends(get_db)):
    """删除工程配置"""
    config = db.query(ProjectConfig).get(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    # 同步删除对应的 Project
    project = db.query(Project).filter_by(
        product_name=config.product_name,
        version=config.version,
        project_name=config.project_name
    ).first()
    if project:
        db.delete(project)
    db.delete(config)
    db.commit()
    return {"message": "配置已删除"}


@router.post("/upload")
async def upload_project_configs(
    product_name: str = Query(...),
    version: str = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传CSV文件批量导入工程配置，表头：工程,PL,责任人"""
    content = await file.read()
    text = content.decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(text))
    
    imported = 0
    updated = 0
    errors = []
    
    for row_num, row in enumerate(reader, start=2):
        project_name = row.get('工程名', '').strip() or row.get('工程', '').strip()
        if not project_name:
            errors.append(f"第{row_num}行：工程名不能为空")
            continue
        
        pl = row.get('PL', '').strip() or None
        owner = row.get('责任人', '').strip() or None
        
        existing = db.query(ProjectConfig).filter_by(
            product_name=product_name,
            version=version,
            project_name=project_name
        ).first()
        
        if existing:
            if pl is not None:
                existing.pl = pl
            if owner is not None:
                existing.owner = owner
            updated += 1
            # 同步更新 Project 的 owner/pl
            proj = db.query(Project).filter_by(
                product_name=product_name,
                version=version,
                project_name=project_name
            ).first()
            if proj:
                if pl is not None:
                    existing.pl = pl
                if owner is not None:
                    existing.owner = owner
                updated += 1
        else:
            config = ProjectConfig(
                product_name=product_name,
                version=version,
                project_name=project_name,
                pl=pl,
                owner=owner
            )
            db.add(config)
            imported += 1
            proj = db.query(Project).filter_by(
                product_name=product_name,
                version=version,
                project_name=project_name
            ).first()
            if not proj:
                proj = Project(
                    product_name=product_name,
                    version=version,
                    project_name=project_name,
                    status="lost"
                )
                db.add(proj)
    
    db.commit()
    return {"imported": imported, "updated": updated, "errors": errors}


@router.get("/download")
def download_project_configs(
    product_name: str = Query(...),
    version: str = Query(...),
    db: Session = Depends(get_db)
):
    """下载CSV文件导出工程配置"""
    from fastapi.responses import StreamingResponse
    
    configs = db.query(ProjectConfig).filter_by(
        product_name=product_name,
        version=version
    ).all()
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['工程名', 'PL', '责任人', '保留天数'])
    writer.writeheader()
    for c in configs:
        writer.writerow({
            '工程名': c.project_name,
            'PL': c.pl or '',
            '责任人': c.owner or '',
            '保留天数': c.retention_days
        })
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=project_config_{product_name}_{version}.csv"}
    )
