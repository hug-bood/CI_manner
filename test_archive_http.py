import requests
import sqlite3
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000/api/v1"
ARCHIVE_DB_PATH = "./backend/ci_archive.db"  # 根据实际路径调整

PRODUCT = "QingLuan"
VERSION = "QingLuan V100R026C10"
PROJECT = "archive_test_project"
SUITE = "archive_suite"
TEST_NAME = "test_archive_case"

def make_timestamp(days_ago: int):
    dt = datetime.utcnow() - timedelta(days=days_ago)
    return dt.isoformat() + "Z"

def report_status(days_ago: int, status: str):
    payload = {
        "test_project_name": PROJECT,
        "test_suite_name": SUITE,
        "test_name": TEST_NAME,
        "version": VERSION,
        "group_id": "archive-test",
        "project_id": "test-proj",
        "record_id": f"rec-{days_ago}-{status}",
        "subrecord_id": f"sub-{days_ago}",
        "status": status,
        "timestamp": make_timestamp(days_ago)
    }
    resp = requests.post(f"{BASE_URL}/reports", json=payload)
    if resp.status_code == 201:
        print(f"  ✅ 上报 {days_ago} 天前状态: {status}")
    else:
        print(f"  ❌ 上报失败: {resp.text}")

def trigger_archive():
    resp = requests.post(f"{BASE_URL}/admin/trigger-archive")
    if resp.status_code == 200:
        print("  📦 归档任务执行成功")
    else:
        print(f"  ❌ 归档触发失败: {resp.text}")

def query_archive_db():
    conn = sqlite3.connect(ARCHIVE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT failure_date, first_failure_date, consecutive_days, status 
        FROM archived_failures 
        WHERE product_name=? AND version=? AND project_name=? AND suite_name=? AND test_name=?
        ORDER BY failure_date
    """, (PRODUCT, VERSION, PROJECT, SUITE, TEST_NAME))
    rows = cursor.fetchall()
    conn.close()
    return rows

def main():
    print("=" * 60)
    print("测试归档功能（HTTP 触发）")
    print("=" * 60)

    print("\n1. 上报历史数据：")
    # 模拟连续失败：第3天前 fail，第2天前 fail，第1天前（昨天）fail
    report_status(3, "fail")
    report_status(2, "fail")
    report_status(1, "fail")

    print("\n2. 手动触发归档任务（应归档昨天及之前的连续失败）：")
    trigger_archive()

    print("\n3. 查询归档数据库中的记录：")
    rows = query_archive_db()
    if rows:
        print("   failure_date | first_failure_date | consecutive_days | status")
        print("   -------------|-------------------|-----------------|--------")
        for r in rows:
            print(f"   {r[0]} | {r[1]} | {r[2]} | {r[3]}")
    else:
        print("   ⚠️ 未找到归档记录，请检查任务是否正常执行。")

    # 预期：昨天（1天前）的归档记录应显示 first_failure_date 为 3 天前，consecutive_days = 3
    print("\n预期：first_failure_date 应为 3 天前，consecutive_days = 3")

if __name__ == "__main__":
    main()