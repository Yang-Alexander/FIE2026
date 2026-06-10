import json
import re
import os

def load_and_clean_samples(file_paths):
    """加载样例集。将0502数据中的区间字符串(如 "(0.875, 1]") 转换为中位数浮点数"""
    combined = []
    for path in file_paths:
        if not os.path.exists(path):
            print(f"⚠️ 找不到文件: {path}，跳过。")
            continue
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                conf = item.get('confidence', 0.50)
                if isinstance(conf, str) and '(' in conf:
                    nums = re.findall(r"[-+]?\d*\.\d+|\d+", conf)
                    conf = round((float(nums[0]) + float(nums[1])) / 2, 2) if len(nums) == 2 else 0.50
                item['confidence'] = conf
                combined.append(item)
    return combined

def robust_parse(response_text):
    """强力正则解析，充当格式兜底安全网，规避LLM直接输出废话或包含Markdown标记"""
    try:
        fact_match = re.search(r'"factivity"\s*:\s*"(TRUE|FALSE|UNCERTAIN)"', response_text, re.IGNORECASE)
        conf_match = re.search(r'"confidence"\s*:\s*([0-9]*\.?[0-9]+)', response_text)
        
        factivity = fact_match.group(1).upper() if fact_match else "UNCERTAIN"
        confidence = float(conf_match.group(1)) if conf_match else 0.50
        return factivity, confidence
    except Exception:
        return "UNCERTAIN", 0.50