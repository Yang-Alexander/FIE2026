import json
from collections import Counter
import config
from data_utils import robust_parse
from retriever import retrieve_top_k_shots
from api_client import call_nvidia_llm
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
    for _ in range(n_votes):
        response_text = call_nvidia_llm(prompt, temperature=0.60)
        results.append(robust_parse(response_text))
        
    fact_votes = [res[0] for res in results]
    counter = Counter(fact_votes)
    majority_fact = counter.most_common(1)[0][0]
    
    if majority_fact == "UNCERTAIN":
        # 核心修改：将原始的 results 列表一并返回
        return "UNCERTAIN", 0.50, results 
        
    agreed_confs = [res[1] for res in results if res[0] == majority_fact]
    avg_conf = sum(agreed_confs) / len(agreed_confs) if agreed_confs else 0.60
    consistency_ratio = counter[majority_fact] / n_votes
    final_conf = avg_conf * (0.8 + 0.2 * consistency_ratio) 
    
    # 核心修改：将原始的 results 列表一并返回
    return majority_fact, round(max(0.51, min(final_conf, 1.00)), 2), results

def run_evaluation_pipeline(test_data_path, output_path="output.json"):
    print(f"🚀 开始执行全量测试并自动打分 (开启 3 轮深度投票)：当前测试文件 [{test_data_path}]...")
    
    with open(test_data_path, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
        
    print(f"✅ 成功读取测试考卷，共发现 {len(test_data)} 道测试题。")
    
    final_outputs = []
    total_score = 0.0
    
    for idx, item in enumerate(test_data):
        true_fact = item.get('factivity', 'UNCERTAIN')
        true_conf = item.get('confidence', 0.50)
        
        # 核心修改：锁定为 3 轮投票，并接收 raw_votes 返回值
        pred_fact, pred_conf, raw_votes = infer_with_consistency(item, n_votes=1) 
        
        question_score = calculate_score(pred_fact, pred_conf, true_fact, true_conf)
        total_score += question_score
        
        print(f"[{idx+1}/{len(test_data)}] ID={item['id']} | 预测: {pred_fact}({pred_conf}) | 标答: {true_fact}({true_conf}) | 得分: {question_score}")
        
        output_item = item.copy()
        raw_id = item['id']
        if isinstance(raw_id, str):
            digits = "".join(filter(str.isdigit, raw_id))
            processed_id = int(digits) if digits else idx + 1
        else:
            processed_id = int(raw_id)
            
        output_item['id'] = processed_id
        output_item['pred_factivity'] = str(pred_fact)
        output_item['pred_confidence'] = float(pred_conf)
        output_item['score'] = question_score 
        
        # 核心修改：将 3 次投票的明细结构化并存入 JSON
        output_item['votes_detail'] = [
            {"round": i + 1, "factivity": vote[0], "confidence": vote[1]} 
            for i, vote in enumerate(raw_votes)
        ]
        
        final_outputs.append(output_item)
        
    # --- 错题分类与导出 ---
    final_outputs = sorted(final_outputs, key=lambda x: x['id'])

    errors_0_score = []
    errors_sigma_score = []      # 1σ
    errors_sigma2_score = []     # 2σ

    for item in final_outputs:
        score = item['score']
        if score == 0.0:
            errors_0_score.append(item)
        elif abs(score - SIGMA) < 1e-6:
            errors_sigma_score.append(item)
        elif abs(score - SIGMA2) < 1e-6:
            errors_sigma2_score.append(item)
            
    # 保存全量比对文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_outputs, f, ensure_ascii=False, indent=4)
        
    # 保存 0 分错题本
    with open("errors_0_score.json", 'w', encoding='utf-8') as f:
        json.dump(errors_0_score, f, ensure_ascii=False, indent=4)
        
    # 保存 σ 分（相邻偏移）错题本
    with open("errors_sigma_score.json", 'w', encoding='utf-8') as f:
        json.dump(errors_sigma_score, f, ensure_ascii=False, indent=4)
        
    # 保存 2σ 错题本
    with open("errors_sigma2_score.json", 'w', encoding='utf-8') as f:
        json.dump(errors_sigma2_score, f, ensure_ascii=False, indent=4)

    # --- 计算得分百分比 ---
    max_possible_score = len(test_data)
    score_ratio = (total_score / max_possible_score) * 100 if max_possible_score > 0 else 0
    
    perfect_count = (max_possible_score- len(errors_0_score)- len(errors_sigma_score)- len(errors_sigma2_score))

    print("\n" + "="*45)
    print("🏆 评测任务全部结束！成绩单如下：")
    print(f"📊 题目总数: {max_possible_score} 题")
    print(f"🌟 梯度总得分: {total_score:.4f} 分")
    print(f"📈 得分占比 (准确率): {score_ratio:.2f}%")
    print("-" * 45)
    print(f"✅ 完美满分题: {perfect_count} 题")
    print(f"🟡 2σ偏移题 ({SIGMA2}分): {len(errors_sigma2_score)} 题 -> errors_sigma2_score.json")
    print(f"🟠 1σ偏移题 ({SIGMA}分): {len(errors_sigma_score)} 题 -> errors_sigma_score.json")
    print(f"❌ 严重误判题 (0分): {len(errors_0_score)} 题 -> errors_0_score.json")
    print("="*45 + "\n")

if __name__ == "__main__":
    run_evaluation_pipeline(config.TEST_SET_FILE)