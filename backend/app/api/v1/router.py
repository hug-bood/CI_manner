from fastapi import APIRouter
from app.api.v1.endpoints import reports, projects, test_cases, admin, archive, features, auth, project_config, product_version_config, backup

api_router = APIRouter()
api_router.include_router(reports.router, tags=["reports"])
api_router.include_router(projects.router, tags=["projects"])
api_router.include_router(test_cases.router, tags=["test_cases"])
api_router.include_router(admin.router, tags=["admin"])
api_router.include_router(archive.router, tags=["archive"])
api_router.include_router(features.router, tags=["features"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(project_config.router, tags=["project_configs"])
api_router.include_router(product_version_config.router, prefix="/product-version-config", tags=["product_version_config"])
api_router.include_router(backup.router, tags=["backup"])
