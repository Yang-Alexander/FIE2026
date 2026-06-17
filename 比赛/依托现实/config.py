import os

# 1. 输入输出路径配置 (核心修改点：严格隔离题库与测试集)
# 作为题库（3-shot 检索源）的文件
KNOWLEDGE_BASE_FILE = 'sample.json' 
# 作为正式考卷的文件
TEST_SET_FILE = 'dataset_pr_260606.json'       
PROMPT_TEMPLATE_PATH = "prompt_template.txt"

# 2. API 参数配置
NVIDIA_API_KEY = "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"
BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL_NAME = "qwen/qwen3-next-80b-a3b-instruct"

# 3. 动态核心语言学规律
LINGUISTIC_RULEBOOK =r"""
任务：给定 text 和 hypothesis，只判断 text 内部是否支持 hypothesis。输出严格 JSON：{“factivity”:“TRUE”,“confidence”:0.95}。factivity 只能为 TRUE/FALSE/UNCERTAIN。TRUE=text 支持 hypothesis 成立；FALSE=text 支持 hypothesis 不成立；UNCERTAIN=text 完全无法判断。只判断文本内部支持关系，不判断现实世界真伪。

一、最高原则

1. 坚定判断，少用 UNCERTAIN。只要 text 对 hypothesis 有明确支持方向，就必须输出 TRUE 或 FALSE。UNCERTAIN 只在没有任何可用语言线索、无法判断方向时使用。
2. 先判断 hypothesis 是 P 还是非P。若 text 支持 P，而 hypothesis 是 P，判 TRUE；若 text 支持 P，而 hypothesis 是非P，判 FALSE；若 text 支持非P，而 hypothesis 是 P，判 FALSE；若 text 支持非P，而 hypothesis 是非P，判 TRUE。
3. 不要看到弱词就直接 UNCERTAIN。遇到感觉、觉得、认为、相信、估计、猜、猜到、怀疑、疑心、听说、表示、声称、报道、指出、揭露、批评、抱怨、埋怨、怪怨、数落、感叹、羡慕、诧异、悔恨、佩服等，继续看主体、证据、语境、语义层级、P/非P方向、是否有强事实、行动验证、后文反转或特殊增强结构。
4. 参考示例体现任务标注风格。若示例与当前题在触发词、语义层级、否定范围、主体类型、P/非P方向上结构一致，应坚定迁移示例风格。不要因为示例存在差异就直接 UNCERTAIN。
5. 规则优先级：明确否定/明确反事实/查明证实发现认定 > hypothesis 边界与 P/非P方向 > 特殊增强规则 > 普通弱认知/普通言说/普通传闻 > 完全无方向才 UNCERTAIN。
6. 特殊增强规则优先于普通弱词规则。普通“怀疑P”可弱，但“异常证据+专业/现场主体+怀疑P”必须支持P；普通“认为P”可弱，但“人们认为/普遍认为P”支持P；普通“听说P”可弱，但“听说P+行动验证/现场后果”支持P；普通“说P”可弱，但“他说调查证实P”按“调查证实P”处理。

二、confidence 安全区间

只允许使用以下 confidence：
A强支持/强反对：[0.90-0.99]。用于明确事实陈述；明确否定；看见/听见/闻到/感受到；知道/发现/查明/证实/确认/认定；不能否认/不可否认；误以为/轻信/假装/谎称/诬陷；强情绪预设；司法/调查/官方正式结论。
B较强支持/较强反对：[0.78-0.85]。用于专家/机构/专业主体判断；异常证据支撑的怀疑；群体认为/普遍认为；不相信P支持非P；没有人怀疑P；行动验证的听说；图谋/企图未完成；主观评价但语境强支持。
C较弱支持/较弱反对：[0.65-0.72]。用于目击者普通声称；抽象评价；不期待/不指望全称P；弱证据支持；来源较可信但无正式证实。
D弱支持/弱反对：[0.52-0.60]。用于普通人声称；普通传闻；普通个人观点；语境有方向但依据弱。
E无法判断：0.50。只用于 UNCERTAIN。
强制：UNCERTAIN 必须 0.50；TRUE/FALSE 不能 0.50；禁止 0.62、0.75、0.87 及所有安全区间外数字。

三、边界对齐

1. 找到 hypothesis 对应完整命题 P，并判断 hypothesis 是 P 还是非P。
2. 检查人物、宾语、时间、地点、数量、范围、方向、主被动是否一致。明确冲突判 FALSE；只是未提到才 UNCERTAIN。
3. 模态边界：可能、有望、预计、计划、打算、准备、希望、担心、认为、觉得、相信、将会、要、最终会等若被 hypothesis 保留，则按保留后的模态命题判断。text 支持“可能P”，hypothesis 也是“可能P”，判 TRUE；不要改成“P已经发生”。
4. 心理状态边界：若 hypothesis 本身是心理状态、感受、希望、压力、畅快、难过、高兴、羡慕、担子重等，text 直接说主体有该状态，判 TRUE。
5. 评价性复述边界：若 text 直接断言评价、哲理、道德判断，hypothesis 复述该判断，判 TRUE。若 text 只是“某人认为/相信P”，hypothesis 去掉“某人认为/相信”，按认为/相信规则分层判断。
6. 梦境/幻想边界：梦到P、梦见P、幻想P、妄想P通常不推出现实P；hypothesis 是现实P，通常 UNCERTAIN 或 FALSE；hypothesis 是梦到/幻想P，判 TRUE。
7. 愿望边界：希望P、期待P、盼望P、渴望P、担心P通常不推出P已经发生；hypothesis=P 通常 UNCERTAIN；hypothesis 是心理状态本身，判 TRUE。愿望类是少数应保留 UNCERTAIN 的结构，不要强行事实化。

四、强事实触发结构

1. 知识/发现/确认：知道P、得知P、明白P、意识到P、发现P、发觉P、查明P、证实P、确认P、证明P、结果显示P、调查显示P、获悉P、认定P、确定P。hypothesis=P 判 TRUE 0.90-0.99；hypothesis=非P 判 FALSE 0.90-0.99。
2. 感官感知：看到P、看见P、望见P、目睹P、听到P、听见P、听出P、闻到P、闻出P、嗅到P、摸到P、碰见P、遇见P、感受到P、觉察到P。hypothesis=P 判 TRUE 0.90-0.99；hypothesis=非P 判 FALSE 0.90-0.99。
3. 注意到P：正式文本、新闻、外交、会议中“注意到P”支持P。hypothesis=P 判 TRUE；hypothesis=非P 判 FALSE。
4. 承认/坦白/供认：承认P、坦白P、供认P、招认P、认罪P通常支持P。无“虚假供认、屈打成招”等反向标记，判 TRUE 0.90-0.99。
5. 情绪预设：后悔P、悔恨P、庆幸P、高兴P、震惊于P、惊讶P、诧异P、遗憾P、不满P、介意P、厌恶P、生气P、不奇怪P、羡慕P、感叹P、难忘P、不得不感慨P、谁也不能不赞叹P、不能忘了P、佩服P、夸奖P，通常预设P成立。hypothesis=P 判 TRUE；hypothesis=非P 判 FALSE。具体事件/身份/状态：0.90-0.99；主观评价/心理状态：0.78-0.85。
6. 很高兴/荣幸有机会P：访问、会见、接待、出席等语境中，“很高兴有机会P/很荣幸有机会P/很高兴能够P”通常表示P已经发生或正在发生。hypothesis=P 判 TRUE。若有“将来、希望以后、如果有机会”，才不推出P。
7. 结果性认知：猜到P、猜出来P、听出P、看出P、看出来P、由此看出P、不难看出P、可以看出P、领悟到P，比普通“猜测/觉得”强，通常支持P。hypothesis=P 判 TRUE；hypothesis=非P 判 FALSE。
8. 显示/表明/说明/反映/暴露/揭示：X显示P、X表明P、X说明P、X反映P、X暴露P、X揭示P通常支持P。hypothesis=P 判 TRUE；hypothesis=非P 判 FALSE。否定形式“未能反映P/不能证明P”按专门规则。

五、否定认知不否定事实

不知道P、不晓得P、没注意到P、没意识到P、没察觉到P、没觉察到P、没发现P、没认出P、没想到P、未曾意料到P、忘记已经P、猜不到P，通常预设P成立，只是否定主体知道/意识到P。hypothesis=P 判 TRUE；hypothesis=非P 判 FALSE。已发生事实、身份事实、明确事件：0.90-0.99；心理状态、抽象评价：0.78-0.85。
注意：“不知道是否P/不知道会不会P”不推出P，通常 UNCERTAIN；“忘记要P”不推出P已经发生。

六、不相信 / 不认为 P

1. text = 不相信P / 不认为P / 并不相信P / 并不认为P。若 P 是观点、预测、判断、评价，且 hypothesis=非P，判 TRUE 0.78-0.85；hypothesis=P，判 FALSE 0.78-0.85。
2. 反预期事实型：若P是已发生事实、身份事实、隐藏事实、表演能力，且有“居然、原来、竟然、其实、没认出、隐藏身份”等线索，则“不相信P/没想到P/没认出P”预设P成立。hypothesis=P 判 TRUE；hypothesis=非P 判 FALSE。
3. 无法区分时：有“居然/原来/竟然/其实/没认出/隐藏身份”按反预期事实；否则按观点否定。

七、反事实和反叙实

1. 错误认知：错误地认为P、误以为P、轻信P、错把X当Y、以为P但其实非P。hypothesis=P 判 FALSE；hypothesis=非P 判 TRUE。
2. 假装/伪装：假装P、装作P、伪装成P、冒充P、佯装P。若P是真实身份、真实状态、真实心理，hypothesis=P 判 FALSE；若P只是外在动作表现，如假装哭、假装挣扎、假装睡觉，hypothesis描述表面动作可 TRUE；若hypothesis说“真的P/确实P”，判 FALSE。
3. 谎称/诬陷/捏造/嫁祸：谎称P、诬陷P、捏造P、编造P、嫁祸P通常支持P不成立。hypothesis=P 判 FALSE；hypothesis=非P 判 TRUE。
4. 吹嘘/自称/夸口：吹嘘P、自称P、夸口P默认削弱P，不自动 FALSE。若无反证，通常 UNCERTAIN 或弱判断；若出现“被揭穿、其实没有、虚张声势、骗人的”，判 FALSE。“不是吹嘘P”不否定P；若有正面依据，hypothesis=P 判 TRUE。
5. 不能想象/不敢相信P：若语境是反预期事实，支持P；若后文明确否认P，如“不可能、不会、上帝不会让P发生”，支持非P。按后文方向坚定判断。

八、认为 / 觉得 / 感觉 / 相信 P

1. 个人主观认为/觉得/感觉/相信P：若P是外部事实且无依据，支持较弱，可 TRUE 0.52-0.72 或 UNCERTAIN；若hypothesis=非P，也可 FALSE 0.52-0.72 或 UNCERTAIN。有方向时不要直接 UNCERTAIN。
2. 群体共识型：人们认为P、大家认为P、普遍认为P、都觉得P、公认P、谁都知道P、没人怀疑P，通常支持P。hypothesis=P 判 TRUE 0.78-0.85；hypothesis=非P 判 FALSE 0.78-0.85。
3. 专家/机构/官方/专业主体认为或指出P：若P属于其专业领域或职责范围，支持P。hypothesis=P 判 TRUE 0.78-0.85；hypothesis=非P 判 FALSE 0.78-0.85。若有研究、数据、现场、调查、检测支撑，可升到 0.90-0.99。
4. 带错误修饰的认为P：偏激地认为P、主观地认为P、错误地认为P、轻信P、误以为P、头脑简单地认为P，不支持P，通常支持非P或至少反对P。hypothesis=P 判 FALSE 或 UNCERTAIN；hypothesis=非P 判 TRUE 或 UNCERTAIN。若修饰词明确表示错误，优先 TRUE/FALSE，不要 UNCERTAIN。
5. 感觉P：若P是自身心理状态、压力、希望、畅快、担子重、感受本身，判 TRUE；若P是亲身互动中的态度判断，如“感觉他没有避开她/感觉他有敌意”，可判 TRUE 0.78-0.85；若P是遥远外部事实且无依据，才考虑 UNCERTAIN。

九、怀疑 / 疑心 / 估计 / 估摸 / 猜测 P

1. 普通怀疑/猜测P：无证据、无专业身份、无后文验证时，通常 UNCERTAIN 或弱支持。但不要机械 UNCERTAIN；若hypothesis是非P，而text明显倾向P，可判 FALSE。
2. 异常证据支撑的怀疑P，优先于普通怀疑规则。同时满足以下条件时，必须判 TRUE/FALSE：A主体是专业主体或现场主体，如机长、技术人员、医生、维修人员、调查人员、目击者、当事人；B text 给出异常证据，如明确撞击声、异常读数、物理痕迹、身体症状、现场损坏、巨额欠款、报案、跑得吃力、身体臃肿等；C异常证据与P有强关联；D P是具体故障、损伤、疾病、事故、身份、现场异常；E后文没有推翻P。满足 A-E：hypothesis=P 判 TRUE 0.78-0.85；hypothesis=非P 判 FALSE 0.78-0.85。
3. 估计P + 现实依据：若前文有节假日、天气、客流、销售、历史趋势、现场状况等依据，估计P可支持P。hypothesis=P 判 TRUE 0.65-0.85；hypothesis=非P 判 FALSE 0.65-0.85。
4. 后文反转：若 text 先“猜测/估计/怀疑/以为P”，后文“但/然而/不料/后来发现/结果证明/最终确定Q”，且Q反驳P，则以后文为准。hypothesis=P 判 FALSE；hypothesis=Q 判 TRUE。

十、言说 / 报道 / 声称 / 听说

1. 普通说/表示/声称/回忆P：不是最强事实，但有方向。普通人声称P：TRUE 0.52-0.60 或 0.65-0.72；目击者/当事人/幸存者回忆P：TRUE 0.65-0.85；官方/专家/机构表示P：TRUE 0.78-0.85；调查证实/查明/结果显示P：TRUE 0.90-0.99。hypothesis=非P 时按相反方向判 FALSE。
2. 外层言说不覆盖内层强事实：如果“他说/报道/表示”的内容中包含看到、听到、发现、查明、证实、承认、后悔、羡慕、感叹、显示、说明等强结构，按内层强结构判断，不因外层“说”而 UNCERTAIN。
3. 目击者/当事人说 + 感知动词：目击者说看到/听到P、当事人说看见P、记者亲眼看到P，通常支持P。hypothesis=P 判 TRUE 0.78-0.95。
4. 揭露/揭示/披露/曝光P：无反向标记时支持P。hypothesis=P 判 TRUE 0.78-0.95；hypothesis=非P 判 FALSE。
5. 听说P：普通听说P较弱，但若有行动验证、现场后果、赶去处理、报警、救人、捐款、前来劝架、也被打、送医等，支持P。hypothesis=P 判 TRUE 0.65-0.85；hypothesis=非P 判 FALSE。
6. 传说/故事/小说：若 text 在传说、故事、小说内部直接叙述P，按文本世界判 TRUE；若只是“据说P”且无叙事承接，可低置信或 UNCERTAIN。

十一、批评 / 抱怨 / 责怪 / 评价

1. 批评P：若P有具体事实核，如未履行承诺、拖欠工资、违法、迟到、打碎东西、不能兑现，通常支持P。hypothesis=P 判 TRUE；hypothesis=非P 判 FALSE。若P是宏观政治评价、价值立场，可低置信 TRUE/FALSE，但尽量判断方向。
2. 怪怨/责怪/埋怨 + 具体已发生事件P：通常预设P发生。hypothesis=P 判 TRUE 0.90-0.99；hypothesis=非P 判 FALSE 0.90-0.99。“不埋怨P”只是否定埋怨态度，不是否定P。
3. 嫌/抱怨/埋怨 + 具体可感知P：如饭菜太咸、天气太冷、屋子太吵、衣服太小，通常支持P。hypothesis=P 判 TRUE；hypothesis=非P 判 FALSE。
4. 群体抱怨 + 具体后果：大家抱怨P、常听人抱怨P，若有后果、损失、异常、普遍情况、后文回指“这种情况/这种问题”，支持P。hypothesis=P 判 TRUE 0.65-0.85。
5. 不会/不再 + 叹息/抱怨/感慨/觉得 + P：是否定主体表达或持有评价P。hypothesis=P 通常 FALSE；hypothesis=非P 通常 TRUE。

十二、希望 / 期待 / 盼望 / 计划 / 图谋

1. 希望/期待/盼望/渴望/担心P：通常不推出P已发生。hypothesis=P 通常 UNCERTAIN；hypothesis=“主体希望/期待/担心P”判 TRUE。这是少数保留 UNCERTAIN 的结构。
2. 不期待/不指望/不奢望 + 全称P：如不期待每个A都P、不指望所有A都P、不奢望人人都P。hypothesis=全称P，判 FALSE 0.65-0.72；hypothesis=并非全称P，判 TRUE 0.65-0.72。
3. 计划/打算/准备/拟/将要/即将/为了/旨在P：通常不推出P已完成。若 hypothesis 保留计划/将要/准备等模态，判 TRUE；若 hypothesis 断言P已完成，通常 UNCERTAIN；若语境显示未遂或被阻止，判 FALSE。
4. 原本/事先/起初并未准备/打算/计划P：支持该阶段没有准备/打算/计划P。若 hypothesis 表达“当时/事先/原本没有准备P”或“没有有意识地P”，判 TRUE 0.78-0.85。若 hypothesis 断言最终没有P，需看后文；无后文可 UNCERTAIN。
5. 图谋/企图/试图/妄图/打算P：只支持意图或尝试，不支持完成。hypothesis=P已完成，通常 UNCERTAIN；若语境未遂/被阻止，判 FALSE；hypothesis=没有完成P，判 TRUE 0.78-0.85。

十三、可能 / 条件 / 未来

1. 可能P：若 hypothesis 删除“可能”直接断言P，通常 UNCERTAIN；若 hypothesis 保留“可能P”，判 TRUE。
2. 你可能不信，P / 令人难以置信的是P：通常是在引出反预期事实，支持P。hypothesis=P 判 TRUE。
3. 要看到/应当明白/必须认识到P：议论、政治、公告、评论语境中通常支持P。hypothesis=P 判 TRUE 0.78-0.95。
4. 没有人怀疑P / 谁也不怀疑P：通常支持P为共识。hypothesis=P 判 TRUE 0.78-0.85；hypothesis=非P 判 FALSE。
5. 由此可见/不难看出/势必P：若前文给出事实前提，支持P。hypothesis=P 判 TRUE。
6. 条件句：如果P就Q、假如P、倘若P、只要P，通常不推出P或Q，除非 text 另说明条件已经满足。反事实条件“如果当时P，就不会Q”常暗示当时没有P。

十四、否定 / 失败 / 阻止

1. 明确否定：不P、没P、没有P、未P、并未P、从未P。hypothesis=P 判 FALSE；hypothesis=非P 判 TRUE。confidence 0.90-0.99。
2. 未能/没能/失败/没有成功P：支持P未成功。hypothesis=P完成 判 FALSE；hypothesis=没有完成P 判 TRUE。
3. 阻止/防止/避免/制止P：通常表示P没有发生或被阻止。hypothesis=P 判 FALSE；hypothesis=非P 判 TRUE。但“试图阻止P”不一定成功。
4. 差点/险些P：通常表示P没发生。hypothesis=P 判 FALSE；hypothesis=非P 判 TRUE。“差点没P”通常表示P最后发生。
5. 否认P：普通“否认P”只是否定言说，较弱。不能否认/不可否认/否认不了P强支持P。hypothesis=P 判 TRUE 0.90-0.99；hypothesis=非P 判 FALSE。

十五、没有证明 / 不能证明 / 未能反映

1. 没有证明/不能证明/未能证明P：只是否定证据关系。若无其他语气，通常 UNCERTAIN；若语境是强反驳，如“一点也没有证明我是胡说”“难以证明中国冰雪运动火起来”，可以倾向非P。hypothesis=P 判 FALSE 0.52-0.85；hypothesis=非P 判 TRUE 0.52-0.85。
2. 不能证明非P：支持P的力度较弱；若上下文立场强，可判 TRUE 0.52-0.72，不要高置信；无方向才 UNCERTAIN。
3. 未能反映出P / 不能反映P：通常不支持P。若语境倾向否定P，可判 FALSE。hypothesis=P 判 FALSE 或 UNCERTAIN；hypothesis=非P 判 TRUE 或 UNCERTAIN。优先看语境方向，尽量给 TRUE/FALSE。

十六、时间 / 状态变化

1. 已经P、曾经P、昨天P、去年P支持过去P。
2. 曾经P不推出现在仍P。
3. 开始P通常推出P发生。
4. 继续P通常推出过去P且现在仍P。
5. 停止P通常推出过去P、现在不P。
6. 恢复P通常推出过去P，中间停止，现在又P。
7. 成为P通常推出现在是P。
8. 曾任P只推出过去是P。
9. 快要/即将/将要P不推出P已发生。
10. 过去P后来改善，不否定过去P；若hypothesis无时间限定，按text语境判断。

十七、人物 / 指代 / 范围 / 数量

1. 人物、对象、时间、地点、数量、方向、主被动必须对齐。明确冲突判 FALSE；只是没提到，才 UNCERTAIN。
2. 中文代词不要机械最近主语优先。结合称呼语、直接引语、第二人称、事件因果判断。直接引语中的“你”可回指前文叙述中的“他”。
3. 职业身份泛化：个体是某职业或群体代表，hypothesis 用“老师/农民/球员/记者”等泛称承接，无冲突时不要判错。
4. 范围包含：所有A都P → 某个A P，TRUE；某些A P → 所有A P，通常 UNCERTAIN。出入境人数增加，在本任务中通常可支持出境或入境增加，除非 text 明确限定相反。不要过度使用严格数学逻辑导致 UNCERTAIN。
5. 数量：几名不能推出三名；三名可推出几名；超过十人可推出多人。

十八、小说 / 故事 / 传说

1. 小说、故事、传说、历史叙述内部直接叙述P，按文本世界判 TRUE。
2. 梦境、幻想、假装边界仍要保留。
3. 据说P、传闻P若只是来源标记且无叙事承接，低置信或 UNCERTAIN；若后文作为故事事实展开，判 TRUE。

十九、输出前检查

输出前检查：hypothesis 是 P 还是非P；text 支持 P 还是非P；是否因为弱词过度保守；是否命中特殊增强规则；是否有异常证据+专业/现场主体；是否是群体认为/普遍认为；是否是“不相信P”但 hypothesis=非P；是否是愿望/盼望/希望P，不应推出P；是否是计划/图谋P，不应推出完成P；是否是没意识到/没想到P，反而预设P；是否是后文反转推翻前文猜测；是否有明确否定；是否把“没有证明P”误判为强P；是否把“没有证明P”在强反驳语气下过度UNCERTAIN；confidence 是否在安全区间；UNCERTAIN 是否只在完全无法判断时使用。

最终只输出严格 JSON，不输出解释、Markdown 或多余文本。
"""