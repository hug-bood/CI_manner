from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.database import SessionLocal
from app.models.project import Project

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
    scheduler.add_job(
        reset_projects_to_lost,
        trigger=CronTrigger(hour=3, minute=0),
        id="daily_lost_reset",
        replace_existing=True
    )
    scheduler.start()