from datetime import date, timedelta
from sqlalchemy import func

from app.models.project import Project
from app.models.test_case import TestCase
from app.models.archive import ArchivedFailure, TestCaseExecutionHistory
from app.core.database import SessionLocal, ArchiveSessionLocal

def archive_daily_failures():
    """
    每日归档任务：
    1. 获取所有未完成的用例（状态非 'pass'），归档到历史归档库。
    2. 计算每个用例的连续失败天数及连续失败起始日期。
    3. 插入归档记录。
    """
    db = SessionLocal()
    archive_db = ArchiveSessionLocal()

    try:
        today = date.today()
        yesterday = today - timedelta(days=1)

        failures = db.query(
            TestCase,
            Project.product_name,
            Project.version,
            Project.project_name
        ).join(
            Project, TestCase.project_id == Project.id
        ).filter(
            TestCase.status.in_(['fail', 'lost', 'processing'])
        ).all()

        for tc, product_name, version, project_name in failures:
            # 查找前一天的归档记录，计算连续失败天数
            prev_archive = archive_db.query(ArchivedFailure).filter(
                ArchivedFailure.product_name == product_name,
                ArchivedFailure.version == version,
                ArchivedFailure.project_name == project_name,
                ArchivedFailure.test_name == tc.test_name,
                ArchivedFailure.failure_date == yesterday
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
                    is_analyzed=tc.is_analyzed,
                    failure_reason=tc.failure_reason,
                    owner=tc.owner,
                    pl=tc.pl
                )
                archive_db.add(archive_entry)

        archive_db.commit()
        print(f"[{today}] Archived {len(failures)} failure cases for {yesterday}")
    except Exception as e:
        archive_db.rollback()
        print(f"Archive job failed: {e}")
    finally:
        db.close()
        archive_db.close()


def daily_reset():
    """
    每日重置任务（完整流程）：
    1. 归档所有未完成的用例到历史归档库
    2. 清除所有工程的用例数据
    3. 将所有工程状态置为 lost，重置统计字段
    """
    db = SessionLocal()
    archive_db = ArchiveSessionLocal()

    try:
        today = date.today()
        yesterday = today - timedelta(days=1)

        # ===== Step 1: 归档所有未完成用例 =====
        failures = db.query(
            TestCase,
            Project.product_name,
            Project.version,
            Project.project_name
        ).join(
            Project, TestCase.project_id == Project.id
        ).filter(
            TestCase.status.in_(['fail', 'lost', 'processing'])
        ).all()

        archived_count = 0
        for tc, product_name, version, project_name in failures:
            # 查找前一天的归档记录，计算连续失败天数
            prev_archive = archive_db.query(ArchivedFailure).filter(
                ArchivedFailure.product_name == product_name,
                ArchivedFailure.version == version,
                ArchivedFailure.project_name == project_name,
                ArchivedFailure.test_name == tc.test_name,
                ArchivedFailure.failure_date == yesterday
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
                    is_analyzed=tc.is_analyzed,
                    failure_reason=tc.failure_reason,
                    owner=tc.owner,
                    pl=tc.pl
                )
                archive_db.add(archive_entry)
                archived_count += 1

        archive_db.commit()
        print(f"[{today}] Step 1: Archived {archived_count} failure cases")

        # ===== Step 2: 清除所有用例数据 =====
        deleted_cases = db.query(TestCase).delete()
        db.commit()
        print(f"[{today}] Step 2: Cleared {deleted_cases} test cases")

        # ===== Step 3: 工程状态置为 lost，重置统计字段 =====
        projects = db.query(Project).all()
        for p in projects:
            p.status = 'lost'
            p.total_cases = 0
            p.total_failed_cases = 0
            p.analyzed_failed_cases = 0
            p.failure_reason = None
        db.commit()
        print(f"[{today}] Step 3: Reset {len(projects)} projects to 'lost'")

    except Exception as e:
        archive_db.rollback()
        db.rollback()
        print(f"Daily reset job failed: {e}")
    finally:
        db.close()
        archive_db.close()
