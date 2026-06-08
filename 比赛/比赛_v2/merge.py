import json

file1 = "sample_20260401.json"
file2 = "sample_20260502_avg.json"
output_file = "sample.json"

# 读取第一个 JSON 文件
with open(file1, "r", encoding="utf-8") as f:
    data1 = json.load(f)

# 读取第二个 JSON 文件
with open(file2, "r", encoding="utf-8") as f:
    data2 = json.load(f)

# 检查两个 JSON 是否都是 list
if not isinstance(data1, list) or not isinstance(data2, list):
    raise ValueError("两个 JSON 文件都应该是列表结构，例如：[{}, {}, {}]")

# 合并
merged_data = data1 + data2

# 保存
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(merged_data, f, ensure_ascii=False, indent=2)

print(f"合并完成，已保存为：{output_file}")
print(f"文件1数量：{len(data1)}")
print(f"文件2数量：{len(data2)}")
print(f"合并后数量：{len(merged_data)}")