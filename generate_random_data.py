import requests
import random
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000/api/v1"

# 模拟配置
PRODUCTS = ["QingLuan", "Kunpeng", "TaiShan"]
VERSIONS = {
    "QingLuan": ["QingLuan V100R026C10", "QingLuan V100R027C00"],
    "Kunpeng": ["Kunpeng V2.0.0", "Kunpeng V2.1.0"],
    "TaiShan": ["TaiShan V3.0.1", "TaiShan V3.1.0"]
}
PROJECTS = ["frontend_ci", "backend_service", "e2e_tests", "unit_tests", "integration_suite"]
TEST_NAMES = [
    "test_login", "test_logout", "test_create_user", "test_delete_user",
    "test_update_profile", "test_search", "test_pagination", "test_upload",
    "test_download", "test_authentication", "test_authorization"
]

# 状态权重：pass 50%, fail 30%, lost 10%, processing 10%
STATUS_CHOICES = ["pass", "fail", "lost", "processing"]
STATUS_WEIGHTS = [0.5, 0.3, 0.1, 0.1]

# 是否源码问题概率（仅非 pass 状态有可能）
SOURCE_CODE_ISSUE_RATE = 0.3

# 是否包含 log_url 的概率（30%）
LOG_URL_RATE = 0.3

def random_date(days_back=30):
    delta = timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )
    return (datetime.utcnow() - delta).isoformat() + "Z"

def generate_dts_ticket():
    """生成随机 DTS 单号"""
    prefixes = ["DTS", "BUG", "TASK"]
    return f"{random.choice(prefixes)}-{random.randint(10000, 99999)}"

def generate_report():
    product = random.choice(PRODUCTS)
    version = random.choice(VERSIONS[product])
    project = random.choice(PROJECTS)
    test = random.choice(TEST_NAMES)
    status = random.choices(STATUS_CHOICES, weights=STATUS_WEIGHTS)[0]

    payload = {
        "test_project_name": project,
        "test_name": test,
        "version": version,
        "group_id": f"group-{random.randint(1, 10)}",
        "project_id": f"proj-{random.randint(100, 999)}",
        "record_id": f"rec-{random.randint(1000, 9999)}",
        "subrecord_id": f"sub-{random.randint(100, 999)}",
        "status": status,
        "timestamp": random_date(days_back=7)
    }

    # 随机设置源码问题字段
    if status != "pass" and random.random() < SOURCE_CODE_ISSUE_RATE:
        payload["is_source_code_issue"] = True
        payload["dts_ticket"] = generate_dts_ticket()
    else:
        payload["is_source_code_issue"] = False
        payload["dts_ticket"] = None

    # 随机添加 log_url（指向一个示例 ZIP 文件，需替换为实际可用的 URL）
    if random.random() < LOG_URL_RATE:
        # 注意：以下 URL 为示例，请替换为真实可访问的 ZIP 文件链接
        payload["log_url"] = "https://example.com/sample_logs.zip"

    return payload

def seed_data(total_reports=300):
    print(f"开始生成 {total_reports} 条随机测试数据...")
    success_count = 0
    fail_count = 0

    for i in range(total_reports):
        payload = generate_report()
        try:
            resp = requests.post(f"{BASE_URL}/reports", json=payload)
            if resp.status_code == 201:
                success_count += 1
            else:
                fail_count += 1
                print(f"失败: {resp.status_code} - {resp.text}")
        except Exception as e:
            fail_count += 1
            print(f"异常: {e}")

        if (i + 1) % 50 == 0:
            print(f"已处理 {i + 1} 条...")

    print(f"\n生成完成！成功: {success_count}, 失败: {fail_count}")

if __name__ == "__main__":
    seed_data(300)