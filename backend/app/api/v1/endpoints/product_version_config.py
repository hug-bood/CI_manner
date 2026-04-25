from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.product_version_config import ProductVersionConfig
from pydantic import BaseModel

router = APIRouter()


class ProductVersionConfigItem(BaseModel):
    product_name: str
    version: str
    retention_days: int = 30

    class Config:
        from_attributes = True


class ProductVersionConfigUpdate(BaseModel):
    retention_days: Optional[int] = None


@router.get("", response_model=ProductVersionConfigItem)
def get_product_version_config(
    product_name: str = Query(...),
    version: str = Query(...),
    db: Session = Depends(get_db)
):
    """获取产品版本配置（含保留天数）"""
    config = db.query(ProductVersionConfig).filter(
        ProductVersionConfig.product_name == product_name,
        ProductVersionConfig.version == version
    ).first()
    if config:
        return ProductVersionConfigItem(
            product_name=config.product_name,
            version=config.version,
            retention_days=config.retention_days
        )
    # 未配置则返回默认值
    return ProductVersionConfigItem(
        product_name=product_name,
        version=version,
        retention_days=30
    )


@router.patch("", response_model=ProductVersionConfigItem)
def update_product_version_config(
    product_name: str = Query(...),
    version: str = Query(...),
    data: ProductVersionConfigUpdate = None,
    db: Session = Depends(get_db)
):
    """更新产品版本配置"""
    config = db.query(ProductVersionConfig).filter(
        ProductVersionConfig.product_name == product_name,
        ProductVersionConfig.version == version
    ).first()
    if not config:
        # 不存在则创建
        config = ProductVersionConfig(
            product_name=product_name,
            version=version,
            retention_days=data.retention_days if data and data.retention_days is not None else 30
        )
        db.add(config)
    else:
        if data and data.retention_days is not None:
            config.retention_days = data.retention_days
    db.commit()
    db.refresh(config)
    return ProductVersionConfigItem(
        product_name=config.product_name,
        version=config.version,
        retention_days=config.retention_days
    )
