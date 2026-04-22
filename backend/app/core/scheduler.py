from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from app.core.database import SessionLocal
from app.models.project import Project
from app.services.archive_service import archive_daily_failures

def reset_projects_to_lost():
    db = SessionLocal()
    try:
        db.query(Project).update({Project.status: "lost"})
        db.commit()
        print(f"[{datetime.now()}] All projects set to 'lost'.")
    except Exception as e:
        print(f"Error resetting projects: {e}")
    finally:
        db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()

    # 归档任务：每天凌晨 2:50 执行
    scheduler.add_job(
        archive_daily_failures,
        trigger=CronTrigger(hour=2, minute=50),
        id="archive_daily_failures",
        replace_existing=True
    )

    # 重置 lost 任务：每天凌晨 3:00 执行
    scheduler.add_job(
        reset_projects_to_lost,
        trigger=CronTrigger(hour=3, minute=0),
        id="daily_lost_reset",
        replace_existing=True
    )

    scheduler.start()