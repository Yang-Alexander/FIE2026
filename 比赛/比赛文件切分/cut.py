import json
import math

INPUT_FILE = "dataset_pr_260606.json"
NUM_PARTS = 5

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# 确保最外层是 list
if not isinstance(data, list):
    raise ValueError("这个 JSON 文件最外层必须是 list，例如：[{}, {}, {}]")

total = len(data)
part_size = math.ceil(total / NUM_PARTS)

for i in range(NUM_PARTS):
    start = i * part_size
    end = start + part_size
    part_data = data[start:end]

    output_file = f"dataset_pr_260606_v{i + 1}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(part_data, f, ensure_ascii=False, indent=4)

    print(f"{output_file} 保存完成，共 {len(part_data)} 条")

print("全部分割完成")