import json

OUTPUT_0="errors_0_score.json"
OUTPUT_sigma="errors_sigma_score.json"

# 保存 0 分错题本
with open(OUTPUT_0, 'r', encoding='utf-8') as f:
    score_0=json.load(f)
    
# 保存 0.6827 分（相邻偏移）错题本
with open(OUTPUT_sigma, 'r', encoding='utf-8') as f:
    score_sigma=json.load(f)

print(len(score_0))
print(len(score_sigma))

