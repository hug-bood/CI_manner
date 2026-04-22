from fastapi import APIRouter
from app.services.archive_service import archive_daily_failures

router = APIRouter()

@router.post("/admin/trigger-archive")
def trigger_archive():
    """
    测试接口：手动触发归档任务（归档昨天的失败数据）
    """
    archive_daily_failures()
    return {"message": "Archive job triggered successfully"}