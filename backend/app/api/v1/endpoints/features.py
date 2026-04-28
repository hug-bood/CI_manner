from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from app.core.database import get_db, get_archive_db, ArchiveSessionLocal
from app.models.feature import Feature, ProjectFeatureMapping
from app.models.project import Project
from app.models.archive import ArchivedFailure

router = APIRouter(prefix="/features", tags=["features"])


def _sync_archive_feature_name(project_name: str, product_name: str, feature_names: str, archive_db: Session):
    """同步更新归档表中该工程的 feature_name（跨所有版本）"""
    archive_db.query(ArchivedFailure).filter(
        ArchivedFailure.project_name == project_name,
        ArchivedFailure.product_name == product_name
    ).update({ArchivedFailure.feature_name: feature_names})


def _get_project_feature_names(project_id: int, db: Session) -> str:
    """获取工程关联的所有特性名，逗号分隔"""
    mappings = db.query(ProjectFeatureMapping, Feature.feature_name).join(
        Feature, ProjectFeatureMapping.feature_id == Feature.id
    ).filter(ProjectFeatureMapping.project_id == project_id).all()
    return ','.join([name for _, name in mappings])


class FeatureItem(BaseModel):
    id: int
    product_name: str
    version: str
    feature_name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class FeatureCreate(BaseModel):
    product_name: str
    version: str
    feature_name: str
    description: Optional[str] = None


class FeatureUpdate(BaseModel):
    feature_name: Optional[str] = None
    description: Optional[str] = None


class ProjectFeatureBinding(BaseModel):
    project_id: int
    feature_id: int


class FeatureListResponse(BaseModel):
    items: List[FeatureItem]
    total: int


@router.get("", response_model=FeatureListResponse)
def list_features(
    product_name: Optional[str] = Query(None),
    version: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取特性列表"""
    query = db.query(Feature)
    if product_name:
        query = query.filter(Feature.product_name == product_name)
    if version:
        query = query.filter(Feature.version == version)
    features = query.order_by(Feature.feature_name).all()
    return FeatureListResponse(items=features, total=len(features))


@router.post("", response_model=FeatureItem, status_code=201)
def create_feature(data: FeatureCreate, db: Session = Depends(get_db)):
    """创建特性"""
    existing = db.query(Feature).filter_by(
        product_name=data.product_name,
        version=data.version,
        feature_name=data.feature_name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Feature already exists")
    feature = Feature(
        product_name=data.product_name,
        version=data.version,
        feature_name=data.feature_name,
        description=data.description
    )
    db.add(feature)
    db.commit()
    db.refresh(feature)
    return feature


@router.patch("/{feature_id}", response_model=FeatureItem)
def update_feature(feature_id: int, data: FeatureUpdate, db: Session = Depends(get_db)):
    """更新特性"""
    feature = db.query(Feature).get(feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    if data.feature_name is not None:
        feature.feature_name = data.feature_name
    if data.description is not None:
        feature.description = data.description
    db.commit()
    db.refresh(feature)
    # 特性改名时，同步所有绑定工程的归档表 feature_name
    bindings = db.query(ProjectFeatureMapping).filter_by(feature_id=feature_id).all()
    archive_db = ArchiveSessionLocal()
    try:
        for b in bindings:
            project = db.query(Project).get(b.project_id)
            if project:
                fn = _get_project_feature_names(b.project_id, db)
                _sync_archive_feature_name(project.project_name, project.product_name, fn, archive_db)
        archive_db.commit()
    finally:
        archive_db.close()
    return feature


@router.delete("/{feature_id}")
def delete_feature(feature_id: int, db: Session = Depends(get_db)):
    """删除特性"""
    feature = db.query(Feature).get(feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    bindings = db.query(ProjectFeatureMapping).filter_by(feature_id=feature_id).all()
    project_ids = [b.project_id for b in bindings]
    db.query(ProjectFeatureMapping).filter_by(feature_id=feature_id).delete()
    db.delete(feature)
    db.commit()
    archive_db = ArchiveSessionLocal()
    try:
        for pid in project_ids:
            project = db.query(Project).get(pid)
            if project:
                fn = _get_project_feature_names(pid, db)
                _sync_archive_feature_name(project.project_name, project.product_name, fn, archive_db)
        archive_db.commit()
    finally:
        archive_db.close()
    return {"message": "Feature deleted"}


@router.post("/bind")
def bind_project_feature(data: ProjectFeatureBinding, db: Session = Depends(get_db)):
    """绑定工程到特性"""
    project = db.query(Project).get(data.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    feature = db.query(Feature).get(data.feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    existing = db.query(ProjectFeatureMapping).filter_by(
        project_id=data.project_id, feature_id=data.feature_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Binding already exists")
    binding = ProjectFeatureMapping(project_id=data.project_id, feature_id=data.feature_id)
    db.add(binding)
    db.commit()
    # 同步归档表 feature_name
    feature_names = _get_project_feature_names(data.project_id, db)
    archive_db = ArchiveSessionLocal()
    try:
        _sync_archive_feature_name(project.project_name, project.product_name, feature_names, archive_db)
        archive_db.commit()
    finally:
        archive_db.close()
    return {"message": "Project bound to feature"}


@router.post("/unbind")
def unbind_project_feature(data: ProjectFeatureBinding, db: Session = Depends(get_db)):
    """解绑工程与特性"""
    binding = db.query(ProjectFeatureMapping).filter_by(
        project_id=data.project_id, feature_id=data.feature_id
    ).first()
    if not binding:
        raise HTTPException(status_code=404, detail="Binding not found")
    project = db.query(Project).get(data.project_id)
    db.delete(binding)
    db.commit()
    # 同步归档表 feature_name
    if project:
        feature_names = _get_project_feature_names(data.project_id, db)
        archive_db = ArchiveSessionLocal()
        try:
            _sync_archive_feature_name(project.project_name, project.product_name, feature_names, archive_db)
            archive_db.commit()
        finally:
            archive_db.close()
    return {"message": "Project unbound from feature"}


@router.get("/projects/{feature_id}")
def get_feature_projects(feature_id: int, db: Session = Depends(get_db)):
    """获取特性下的工程列表"""
    feature = db.query(Feature).get(feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    bindings = db.query(ProjectFeatureMapping).filter_by(feature_id=feature_id).all()
    project_ids = [b.project_id for b in bindings]
    projects = db.query(Project).filter(Project.id.in_(project_ids)).all() if project_ids else []
    return {"items": [{"id": p.id, "name": p.project_name, "status": p.status} for p in projects]}
