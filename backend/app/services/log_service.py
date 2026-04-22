import os
import zipfile
import tempfile
import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3

# 禁用 SSL 警告
urllib3.disable_warnings(InsecureRequestWarning)

# 日志存储根目录（可通过环境变量配置）
LOG_STORAGE_ROOT = os.getenv("LOG_STORAGE_ROOT", "./logs")

def download_and_extract_zip(url: str, test_case_id: int) -> str:
    """
    下载 zip 文件并解压到以 test_case_id 命名的目录中。
    返回解压后的目录绝对路径。
    若下载失败或文件损坏，抛出异常。
    """
    # 创建临时文件用于下载
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
        tmp_path = tmp_file.name

    try:
        # 下载文件（禁用 SSL 验证）
        response = requests.get(url, stream=True, verify=False, timeout=30)
        response.raise_for_status()
        with open(tmp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # 创建目标解压目录
        dest_dir = os.path.join(LOG_STORAGE_ROOT, str(test_case_id))
        os.makedirs(dest_dir, exist_ok=True)

        # 解压 zip 文件
        with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
            zip_ref.extractall(dest_dir)

        return os.path.abspath(dest_dir)

    except Exception as e:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise e

    finally:
        # 无论成功与否，删除临时 zip 文件
        if os.path.exists(tmp_path):
            os.remove(tmp_path)