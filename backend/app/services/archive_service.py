from datetime import date, timedelta
from sqlalchemy import func

from app.models.project import Project
from app.models.test_case import TestCase
from app.models.archive import ArchivedFailure
from app.core.database import SessionLocal, ArchiveSessionLocal

def archive_daily_failures():
    """
    每日归档任务：
    1. 获取昨天所有未解决的用例（状态非 'pass'）。
    2. 计算每个用例的连续失败天数及连续失败起始日期。
    3. 若昨天状态为失败/丢失/处理中，则插入归档记录。
    """
    db = SessionLocal()
    archive_db = ArchiveSessionLocal()

    try:
        yesterday = date.today() - timedelta(days=1)

        failures = db.query(
            TestCase,
            Project.product_name,
            Project.version,
            Project.project_name
        ).join(
            Project, TestCase.project_id == Project.id
        ).filter(
            TestCase.status.in_(['fail', 'lost', 'processing']),
            func.date(TestCase.last_report_at) == yesterday
        ).all()

        for tc, product_name, version, project_name in failures:
            prev_day = yesterday - timedelta(days=1)
            prev_archive = archive_db.query(ArchivedFailure).filter(
                ArchivedFailure.product_name == product_name,
                ArchivedFailure.version == version,
                ArchivedFailure.project_name == project_name,
                ArchivedFailure.test_name == tc.test_name,
                ArchivedFailure.failure_date == prev_day
            ).first()

            if prev_archive:
                consecutive = prev_archive.consecutive_days + 1
                first_failure = prev_archive.first_failure_date
            else:
                consecutive = 1
                first_failure = yesterday

            existing = archive_db.query(ArchivedFailure).filter(
                ArchivedFailure.product_name == product_name,
                ArchivedFailure.version == version,
                ArchivedFailure.project_name == project_name,
                ArchivedFailure.test_name == tc.test_name,
                ArchivedFailure.failure_date == yesterday
            ).first()

            if not existing:
                archive_entry = ArchivedFailure(
                    product_name=product_name,
                    version=version,
                    project_name=project_name,
                    test_name=tc.test_name,
                    failure_date=yesterday,
                    first_failure_date=first_failure,
                    consecutive_days=consecutive,
                    status=tc.status,
                    failure_reason=tc.failure_reason,
                    owner=tc.owner,
                    pl=tc.pl
                )
                archive_db.add(archive_entry)

        archive_db.commit()
        print(f"[{date.today()}] Archived failures for {yesterday}")
    except Exception as e:
        archive_db.rollback()
        print(f"Archive job failed: {e}")
    finally:
        db.close()
        archive_db.close()