from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.database import engine, Base, archive_engine, ArchiveBase
from app.api.v1.router import api_router
from app.core.scheduler import start_scheduler

# 导入所有模型以确保表被创建
from app.models import project, test_case, archive

settings = get_settings()

# 创建数据库表
Base.metadata.create_all(bind=engine)
ArchiveBase.metadata.create_all(bind=archive_engine)

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