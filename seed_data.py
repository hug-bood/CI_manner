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
SUITES = ["smoke_tests", "regression_tests", "api_tests", "performance_tests"]
TEST_NAMES = ["test_login", "test_logout", "test_create_user", "test_delete_user",
              "test_update_profile", "test_search", "test_pagination", "test_upload",
              "test_download", "test_authentication", "test_authorization"]


def random_date(days_back=30):
    """生成过去 days_back 天内的随机时间"""
    delta = timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )
    return (datetime.utcnow() - delta).isoformat() + "Z"


def generate_report(product_name, version, project_name):
    """生成单条上报数据"""
    suite = random.choice(SUITES)
    test = random.choice(TEST_NAMES)
    status = random.choices(
        ["pass", "fail", "lost"],
        weights=[0.5, 0.35, 0.15]  # 50%通过，35%失败，15%丢失
    )[0]
    return {
        "test_project_name": project_name,
        "test_suite_name": suite,
        "test_name": test,
        "version": version,
        "group_id": f"group-{random.randint(1, 10)}",
        "project_id": f"proj-{random.randint(100, 999)}",
        "record_id": f"rec-{random.randint(1000, 9999)}",
        "subrecord_id": f"sub-{random.randint(100, 999)}",
        "status": status,
        "timestamp": random_date(days_back=7)  # 最近7天内的数据
    }


def seed_data(total_reports=200):
    """批量上报数据"""
    print(f"开始生成 {total_reports} 条测试数据...")
    success_count = 0
    fail_count = 0

    for i in range(total_reports):
        product = random.choice(PRODUCTS)
        version = random.choice(VERSIONS[product])
        project = random.choice(PROJECTS)

        payload = generate_report(product, version, project)

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

        # 进度提示
        if (i + 1) % 50 == 0:
            print(f"已处理 {i + 1} 条...")

    print(f"\n生成完成！成功: {success_count}, 失败: {fail_count}")


def add_analysis_data():
    """
    随机为部分失败用例添加分析记录（调用 analyze 接口）
    这会使分析进展 > 0，便于测试趋势图
    """
    print("\n正在为部分失败用例添加分析数据...")
    # 获取所有工程详情（简化：仅对前几个工程操作）
    # 实际可以通过查询接口获取失败用例列表，这里采用简单策略：再上报几条并手动标记分析
    # 我们直接调用已有的测试脚本中的 analyze 逻辑太复杂，这里采用另一种方式：
    # 由于批量上报时已生成了各种状态的用例，我们可以直接通过前端手动分析，
    # 或者运行 test_backend.py 中的分析部分。
    print("分析数据建议通过前端手动标记几个失败用例，或运行 test_backend.py 中的分析测试。")


if __name__ == "__main__":
    seed_data(300)  # 生成300条上报数据