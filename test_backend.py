import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api/v1"

def print_response(title, response):
    print(f"\n--- {title} ---")
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)

def test_report():
    payload = {
        "test_project_name": "demo_project",
        "test_suite_name": "smoke_tests",
        "test_name": "test_login",
        "version": "QingLuan V100R026C10",
        "group_id": "g1",
        "project_id": "p1",
        "record_id": "r1",
        "subrecord_id": "s1",
        "status": "fail",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    response = requests.post(f"{BASE_URL}/reports", json=payload)
    print_response("1. 上报失败用例", response)

    payload["test_name"] = "test_logout"
    payload["status"] = "pass"
    response = requests.post(f"{BASE_URL}/reports", json=payload)
    print_response("2. 上报通过用例", response)

    payload["test_name"] = "test_profile"
    payload["status"] = "lost"
    response = requests.post(f"{BASE_URL}/reports", json=payload)
    print_response("3. 上报 lost 用例", response)

    return payload["test_project_name"], payload["version"]

def test_summary(product_name, version):
    version_encoded = version.replace(" ", "%20")
    response = requests.get(f"{BASE_URL}/products/{product_name}/versions/{version_encoded}/summary")
    print_response("4. 获取仪表盘汇总", response)

def test_project_list(product_name, version):
    version_encoded = version.replace(" ", "%20")
    response = requests.get(f"{BASE_URL}/products/{product_name}/versions/{version_encoded}/projects?page=1&size=10")
    print_response("5. 获取工程列表", response)
    return response.json()["items"][0]["id"] if response.status_code == 200 else None

def test_project_detail(project_id):
    response = requests.get(f"{BASE_URL}/projects/{project_id}")
    print_response("6. 获取工程详情", response)
    if response.status_code == 200:
        cases = response.json()["test_cases"]
        fail_case = next((c for c in cases if c["status"] in ["fail", "lost"]), None)
        return fail_case
    return None

def test_update_status(product_name, version, project_name, suite_name, test_name):
    payload = {
        "product_name": product_name,
        "version": version,
        "project_name": project_name,
        "suite_name": suite_name,
        "test_name": test_name,
        "status": "processing"
    }
    response = requests.patch(f"{BASE_URL}/test-cases/status", json=payload)
    print_response("7. 修改用例状态为 processing", response)

def test_analyze(product_name, version, project_name, suite_name, test_name):
    payload = {
        "product_name": product_name,
        "version": version,
        "project_name": project_name,
        "suite_name": suite_name,
        "test_name": test_name,
        "failure_reason": "登录接口超时，需要优化网络配置"
    }
    response = requests.post(f"{BASE_URL}/test-cases/analyze", json=payload)
    print_response("8. 填写失败原因并标记已分析", response)

def main():
    print("=" * 60)
    print("开始测试 CI Management API")
    print("=" * 60)

    project_name, version = test_report()
    product_name = version.split(" ")[0]

    test_summary(product_name, version)

    project_id = test_project_list(product_name, version)

    if not project_id:
        print("\n!!! 未获取到工程ID，请检查上报是否成功")
        return

    fail_case = test_project_detail(project_id)

    if fail_case:
        test_update_status(
            product_name,
            version,
            project_name,
            fail_case["suite_name"],
            fail_case["test_name"]
        )
        test_analyze(
            product_name,
            version,
            project_name,
            fail_case["suite_name"],
            fail_case["test_name"]
        )
        test_summary(product_name, version)
        test_project_detail(project_id)

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()