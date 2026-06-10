import json
import re

INPUT_FILE = "output_merged.json"
OUTPUT_FILE = "output.json"


def round_confidence(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "confidence" and isinstance(value, (int, float)):
                obj[key] = round(value, 2)
            else:
                round_confidence(value)

    elif isinstance(obj, list):
        for item in obj:
            round_confidence(item)


with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

round_confidence(data)

# 先正常输出 JSON
json_text = json.dumps(data, ensure_ascii=False, indent=4)

# 再把 confidence 后面的数字强制格式化成两位小数
def format_confidence(match):
    value = float(match.group(1))
    return f'"confidence": {value:.2f}'

json_text = re.sub(
    r'"confidence":\s*(-?\d+(?:\.\d+)?)',
    format_confidence,
    json_text
)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(json_text)

print(f"处理完成，已保存为 {OUTPUT_FILE}")