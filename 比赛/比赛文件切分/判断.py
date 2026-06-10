import json

INPUT_FILE = "dataset_pr_260606_v1.json"
OUTPUT_FILE = "output1.json"

# 读取 input.json
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

output_data = []

for i, item in enumerate(data, start=1):
    text = item.get("text", "")
    hypothesis = item.get("hypothesis", "")

    print("=" * 60)
    print(f"第 {i} 条")
    print("text:")
    print(text)
    print()
    print("hypothesis:")
    print(hypothesis)
    print()

    # 手动输入 factivity
    while True:
        factivity = input("请输入 factivity（TRUE / FALSE / UNCERTAIN）：").strip().upper()

        if factivity in ["TRUE", "FALSE", "UNCERTAIN"]:
            break
        else:
            print("输入不合法，请输入 TRUE、FALSE 或 UNCERTAIN。")

    # 保留原始数据，并加入/覆盖 factivity
    new_item = item.copy()
    new_item["factivity"] = factivity

    output_data.append(new_item)

# 保存到 output.json
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=4)

print(f"\n完成！结果已保存到 {OUTPUT_FILE}")