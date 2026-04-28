from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from app.services.archive_service import daily_reset

def start_scheduler():
    scheduler = BackgroundScheduler()

    # 每日重置任务：凌晨 3:00 执行
    # 流程：归档未完成用例 → 清除所有用例数据 → 工程状态置为 lost
    scheduler.add_job(
        daily_reset,
        trigger=CronTrigger(hour=3, minute=0),
        id="daily_reset",
        replace_existing=True
    )

    scheduler.start()
