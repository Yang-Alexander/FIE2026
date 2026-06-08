import re

SIGMA = 0.6827
SIGMA2 = 0.9545

def get_interval_index(factivity, confidence):
    """
    将 FIE2026 官方的 9 个叙实性强度区间映射为整数索引：
    0: 强反叙实 FALSE (0.875, 1.00]
    1: 较强反叙实 FALSE (0.75, 0.875]
    2: 较弱反叙实 FALSE (0.625, 0.75]
    3: 弱反叙实 FALSE (0.50, 0.625]
    4: 非叙实 UNCERTAIN 0.50
    5: 弱正叙实 TRUE (0.50, 0.625]
    6: 较弱正叙实 TRUE (0.625, 0.75]
    7: 较强正叙实 TRUE (0.75, 0.875]
    8: 强正叙实 TRUE (0.875, 1.00]
    """
    factivity = str(factivity).strip().upper()
    
    if factivity == "UNCERTAIN":
        return 4
        
    # 兼容第二批样例集中带括号的区间字符串 (如 "(0.875, 1]")
    if isinstance(confidence, str) and '(' in confidence:
        nums = re.findall(r"[-+]?\d*\.\d+|\d+", confidence)
        if len(nums) == 2:
            conf_val = (float(nums[0]) + float(nums[1])) / 2.0
        else:
            conf_val = 0.50
    else:
        # 处理模型输出的浮点数或第一批样例集的浮点数
        try:
            conf_val = float(confidence)
        except (ValueError, TypeError):
            conf_val = 0.50

    if factivity == "FALSE":
        if conf_val > 0.875: return 0
        elif conf_val > 0.75: return 1
        elif conf_val > 0.625: return 2
        else: return 3
        
    elif factivity == "TRUE":
        if conf_val <= 0.625: return 5
        elif conf_val <= 0.75: return 6
        elif conf_val <= 0.875: return 7
        else: return 8
        
    else:
        return 4

def calculate_score(pred_fact, pred_conf, true_fact, true_conf):
    """
    计算单题得分:
    核心规则1：如果极性大类 (TRUE/FALSE/UNCERTAIN) 判断错误，直接得 0 分。
    核心规则2：在极性判断正确的前提下，落在同一置信区间得 1 分，相邻区间得 0.6827 分，跨级得 0 分。
    """
        
    # 如果极性大类一致，再通过索引计算置信度区间的偏移量
    pred_idx = get_interval_index(pred_fact, pred_conf)
    true_idx = get_interval_index(true_fact, true_conf)
    
    diff = abs(pred_idx - true_idx)
    
    if diff == 0:
        return 1.0
    elif diff == 1:
        return SIGMA2
    elif diff == 2:
        return SIGMA
    else:
        return 0.0