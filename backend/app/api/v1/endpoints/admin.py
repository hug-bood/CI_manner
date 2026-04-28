from fastapi import APIRouter
from app.services.archive_service import daily_reset, archive_daily_failures

router = APIRouter()

@router.post("/admin/trigger-daily-reset")
def trigger_daily_reset():
    """
    手动触发每日重置任务（归档未完成用例 → 清除用例数据 → 工程置为 lost）
    """
    daily_reset()
    return {"message": "Daily reset job triggered successfully"}

@router.post("/admin/trigger-archive")
def trigger_archive():
    """
    手动触发归档任务（仅归档，不清除数据）
    """
    archive_daily_failures()
    return {"message": "Archive job triggered successfully"}
