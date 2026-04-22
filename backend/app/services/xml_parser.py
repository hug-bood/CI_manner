import os
import glob
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, List

def parse_custom_xml(file_path: str) -> Optional[Dict[str, Any]]:
    """
    解析自定义格式的 XML 文件：
    <root>
        <test>
            <name>UT_NPU_Event_FUNC_001</name>
            <prio>2</prio>
            <active>active</active>
            <pass>pass</pass>
            <time>1.55ms</time>
            <errmsg></errmsg>
        </test>
        ...
    </root>
    返回统计摘要和详细列表。
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        tests = []
        total = 0
        passed = 0
        failed = 0
        total_time_ms = 0.0

        for test_elem in root.findall("test"):
            total += 1
            name_elem = test_elem.find("name")
            pass_elem = test_elem.find("pass")
            time_elem = test_elem.find("time")
            errmsg_elem = test_elem.find("errmsg")

            name = name_elem.text if name_elem is not None else ""
            pass_value = pass_elem.text.lower() if pass_elem is not None else ""
            time_str = time_elem.text if time_elem is not None else "0ms"
            errmsg = errmsg_elem.text if errmsg_elem is not None else ""

            # 判断是否通过
            is_pass = pass_value == "pass"
            if is_pass:
                passed += 1
            else:
                failed += 1

            # 解析时间（去掉 "ms" 后缀）
            if time_str.endswith("ms"):
                try:
                    total_time_ms += float(time_str[:-2])
                except ValueError:
                    pass

            tests.append({
                "name": name,
                "pass": is_pass,
                "time": time_str,
                "errmsg": errmsg
            })

        summary = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "total_time_ms": round(total_time_ms, 3),
            "details": tests
        }
        return summary

    except Exception as e:
        print(f"XML parsing failed for {file_path}: {e}")
        return None


def find_and_parse_result_xml(log_dir: str) -> Optional[Dict[str, Any]]:
    """
    在解压后的日志目录中查找 result_*.xml 文件，并解析第一个匹配的文件。
    """
    pattern = os.path.join(log_dir, "result_*.xml")
    xml_files = glob.glob(pattern)
    if not xml_files:
        print(f"No result_*.xml found in {log_dir}")
        return None

    xml_file = xml_files[0]
    summary = parse_custom_xml(xml_file)
    return summary