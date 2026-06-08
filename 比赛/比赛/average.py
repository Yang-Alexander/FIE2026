import json
import re

input_file = "sample_20260502.json"
output_file = "sample_20260502_avg.json"


def convert_confidence(value):
    """
    将 confidence 从区间形式转换为区间两端平均数。
    例如：
    "(0.875, 1]" -> 0.94
    "(0.75, 0.875]" -> 0.81
    "0.5" -> 0.50
    """

    # 如果本身是数字
    if isinstance(value, (int, float)):
        return round(float(value), 2)

    # 如果是字符串
    if isinstance(value, str):
        value = value.strip()

        # 匹配区间，例如 "(0.875, 1]"
        match = re.match(r"^[\(\[]\s*([0-9.]+)\s*,\s*([0-9.]+)\s*[\)\]]$", value)
        if match:
            left = float(match.group(1))
            right = float(match.group(2))
            return round((left + right) / 2, 2)

        # 如果是普通数字字符串，例如 "0.5"
        try:
            return round(float(value), 2)
        except ValueError:
            return value

    return value


with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# 如果 JSON 是列表
if isinstance(data, list):
    for item in data:
        if isinstance(item, dict) and "confidence" in item:
            item["confidence"] = convert_confidence(item["confidence"])

# 如果 JSON 是字典
elif isinstance(data, dict):
    if "confidence" in data:
        data["confidence"] = convert_confidence(data["confidence"])

    # 如果字典里嵌套了列表，也可以处理
    for key, value in data.items():
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and "confidence" in item:
                    item["confidence"] = convert_confidence(item["confidence"])

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"处理完成，已保存为：{output_file}")