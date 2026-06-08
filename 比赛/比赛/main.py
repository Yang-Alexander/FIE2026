import json
from collections import Counter
import config
from data_utils import robust_parse
from retriever import retrieve_top_k_shots
from api_client import call_NVIDIA_llm
from evaluator import calculate_score, SIGMA, SIGMA2  # 确保导入了 SIGMA

def build_final_prompt(test_item, retrieved_shots):
    """读取模板文件，执行动态插值替换"""
    with open(config.PROMPT_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        template = f.read()
    shots_str = ""
    for i, shot in enumerate(retrieved_shots):
        shots_str += f"样例 {i+1}:\n主句：{shot['text']}\n被蕴含句：{shot['hypothesis']}\n"
        shots_str += f"推断结果：{{\"factivity\": \"{shot['factivity']}\", \"confidence\": {shot['confidence']}}}\n\n"
    prompt = template.replace("{{LINGUISTIC_RULEBOOK}}", config.LINGUISTIC_RULEBOOK)
    prompt = prompt.replace("{{SHOTS}}", shots_str)
    prompt = prompt.replace("{{TEST_TEXT}}", test_item['text'])
    prompt = prompt.replace("{{TEST_HYPOTHESIS}}", test_item['hypothesis'])
    return prompt

def infer_with_consistency(test_item, n_votes=3):
    """多轮投票校准置信度算法"""
    shots = retrieve_top_k_shots(test_item['text'], k=3)
    prompt = build_final_prompt(test_item, shots)
    
    results = [] # 记录每一轮的原始投票结果
    raw_outputs = []
    for _ in range(n_votes):
        response_text = call_NVIDIA_llm(prompt, temperature=0.60)
        raw_outputs.append(response_text)
        results.append(robust_parse(response_text))
        
    fact_votes = [res[0] for res in results]
    counter = Counter(fact_votes)
    majority_fact = counter.most_common(1)[0][0]
    
    if majority_fact == "UNCERTAIN":
        # 核心修改：将原始的 results 列表一并返回
        return "UNCERTAIN", 0.50, results ,raw_outputs
        
    agreed_confs = [res[1] for res in results if res[0] == majority_fact]
    avg_conf = sum(agreed_confs) / len(agreed_confs) if agreed_confs else 0.60
    consistency_ratio = counter[majority_fact] / n_votes
    final_conf = avg_conf * (0.8 + 0.2 * consistency_ratio) 
    
    # 核心修改：将原始的 results 列表一并返回
    return majority_fact, round(max(0.51, min(final_conf, 1.00)), 2), results, raw_outputs

def run_evaluation_pipeline(test_data_path, output_path="output.json"):
    print(f"🚀 开始执行全量测试并自动打分 (开启 3 轮深度投票)：当前测试文件 [{test_data_path}]...")
    
    with open(test_data_path, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
        
    print(f"✅ 成功读取测试考卷，共发现 {len(test_data)} 道测试题。")
    
    final_outputs = []
    total_score = 0.0
    
    for idx, item in enumerate(test_data):
        
        # 核心修改：锁定为 3 轮投票，并接收 raw_votes 返回值
        pred_fact, pred_conf, raw_votes , raw_outputs= infer_with_consistency(item, n_votes=3) 
        
        question_score = None
        
        print(f"[{idx+1}/{len(test_data)}] ID={item['id']} | 预测: {pred_fact}({pred_conf})")

        raw_id = item['id']
        if isinstance(raw_id, str):
            digits = "".join(filter(str.isdigit, raw_id))
            processed_id = int(digits) if digits else idx + 1
        else:
            processed_id = int(raw_id)

        # 比赛提交文件：必须且只能包含 track / id / factivity / confidence 四个字段
        submit_item = {
            "track": item.get("track", "pr"),
            "id": processed_id,
            "factivity": str(pred_fact),
            "confidence": round(float(pred_conf), 2)
        }

        # 防止格式非法：UNCERTAIN 的 confidence 必须固定为 0.50
        if submit_item["factivity"] == "UNCERTAIN":
            submit_item["confidence"] = 0.50
        else:
            submit_item["confidence"] = max(0.51, min(submit_item["confidence"], 1.00))

        final_outputs.append(submit_item)
                
    # --- 按 id 升序排序，满足提交要求 ---
    final_outputs = sorted(final_outputs, key=lambda x: x['id'])

    # --- 保存比赛提交文件 output.json ---
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_outputs, f, ensure_ascii=False, indent=4)

    print("\n" + "=" * 45)
    print("🏆 预测任务全部结束！")
    print(f"📊 输出条数: {len(final_outputs)} 条")
    print(f"📁 已保存提交文件: {output_path}")
    print("✅ 提交字段: track / id / factivity / confidence")
    print("=" * 45 + "\n")

if __name__ == "__main__":
    run_evaluation_pipeline(config.TEST_SET_FILE, output_path="output.json")