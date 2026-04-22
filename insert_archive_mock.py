import sqlite3
import random
from datetime import date, timedelta

DB_PATH = "./backend/ci_archive.db"  # 请根据实际路径修改

# 模拟基础数据
PRODUCT = "QingLuan"
VERSION = "QingLuan V100R026C10"
PROJECTS = ["frontend_ci", "backend_service", "e2e_tests"]
SUITES = ["smoke_tests", "api_tests", "regression"]
TEST_NAMES = ["test_login", "test_payment", "test_search", "test_upload", "test_profile"]
STATUSES = ["fail", "lost", "processing"]
OWNERS = ["张三", "李四", "王五", None]
PLS = ["赵六", "钱七", None]
FAILURE_REASONS = [
    "连接超时",
    "断言失败：期望值 200，实际 500",
    "数据库死锁",
    "元素未找到",
    None
]

def generate_mock_data(num_records=50):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 清空旧测试数据（可选，若只想追加可注释）
    cursor.execute("DELETE FROM archived_failures WHERE product_name = ? AND version = ?", (PRODUCT, VERSION))

    today = date.today()
    for i in range(num_records):
        # 随机生成连续失败场景
        consecutive_days = random.randint(1, 12)
        failure_date = today - timedelta(days=random.randint(0, 30))
        first_failure_date = failure_date - timedelta(days=consecutive_days - 1)

        project = random.choice(PROJECTS)
        suite = random.choice(SUITES)
        test = random.choice(TEST_NAMES)
        status = random.choice(STATUSES)
        owner = random.choice(OWNERS)
        pl = random.choice(PLS)
        reason = random.choice(FAILURE_REASONS)

        cursor.execute("""
            INSERT OR IGNORE INTO archived_failures 
            (product_name, version, project_name, suite_name, test_name, failure_date, first_failure_date, consecutive_days, status, failure_reason, owner, pl)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            PRODUCT, VERSION, project, suite, test,
            failure_date.isoformat(), first_failure_date.isoformat(),
            consecutive_days, status, reason, owner, pl
        ))

    conn.commit()
    conn.close()
    print(f"已插入 {num_records} 条模拟归档数据到 {DB_PATH}")

if __name__ == "__main__":
    generate_mock_data(50)