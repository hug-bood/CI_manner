from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.database import engine, Base, archive_engine, ArchiveBase
from app.api.v1.router import api_router
from app.core.scheduler import start_scheduler

# 导入所有模型以确保表被创建
from app.models import project, test_case, archive, feature, auth, project_config, product_version_config

settings = get_settings()

# 创建数据库表
Base.metadata.create_all(bind=engine)
ArchiveBase.metadata.create_all(bind=archive_engine)

# 确保唯一约束存在（兼容已有数据库）
with engine.connect() as conn:
    import sqlalchemy
    inspector = sqlalchemy.inspect(engine)
    # 检查索引是否已存在（get_unique_constraints 可能检测不到 CREATE UNIQUE INDEX 创建的索引）
    indexes = [idx['name'] for idx in inspector.get_indexes('project_configs')]
    unique_constraints = [uc['name'] for uc in inspector.get_unique_constraints('project_configs')]
    already_exists = ('uq_project_config' in indexes) or ('uq_project_config' in unique_constraints)
    if not already_exists:
        # 先清理重复数据（保留id最小的记录）
        conn.execute(sqlalchemy.text(
            "DELETE FROM project_configs WHERE id NOT IN ("
            "  SELECT MIN(id) FROM project_configs"
            "  GROUP BY product_name, version, project_name"
            ")"
        ))
        conn.execute(sqlalchemy.text(
            "CREATE UNIQUE INDEX uq_project_config ON project_configs (product_name, version, project_name)"
        ))
        conn.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}