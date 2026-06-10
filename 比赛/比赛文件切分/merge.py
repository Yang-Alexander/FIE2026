import json

INPUT_FILES = [
    "output1.json",
    "output2.json",
    "output3.json",
    "output4.json",
    "output5.json",
]

OUTPUT_FILE = "output_merged.json"

merged_data = []

for file_name in INPUT_FILES:
    with open(file_name, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"{file_name} 的最外层不是 list，不能直接合并")

    merged_data.extend(data)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(merged_data, f, ensure_ascii=False, indent=4)

print(f"合并完成，共 {len(merged_data)} 条，已保存为 {OUTPUT_FILE}")