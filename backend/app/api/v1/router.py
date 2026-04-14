from fastapi import APIRouter
from app.api.v1.endpoints import reports, projects, test_cases

api_router = APIRouter()
api_router.include_router(reports.router, tags=["reports"])
api_router.include_router(projects.router, tags=["projects"])
api_router.include_router(test_cases.router, tags=["test_cases"])