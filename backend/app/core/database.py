from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

settings = get_settings()

# 主业务数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 归档数据库引擎
archive_engine = create_engine(
    settings.ARCHIVE_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.ARCHIVE_DATABASE_URL else {}
)
ArchiveSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=archive_engine)
ArchiveBase = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_archive_db():
    db = ArchiveSessionLocal()
    try:
        yield db
    finally:
        db.close()