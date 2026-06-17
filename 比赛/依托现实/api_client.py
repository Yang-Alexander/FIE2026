from openai import OpenAI
import config

# 初始化 OpenAI 客户端 (指向 NVIDIA 的 API 网关)
client = OpenAI(
    base_url=config.BASE_URL,
    api_key=config.NVIDIA_API_KEY
)

def call_NVIDIA_llm(prompt, temperature=0.60):
    """使用 OpenAI SDK 调用指定的 NVIDIA 模型"""
    try:
        # 注意：为了配合自动化评测提取 JSON，这里将 stream 设为了 False
        completion = client.chat.completions.create(
            model=config.MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            top_p=0.7,
            max_tokens=4096,
            stream=False 
        )
        
        # 提取并返回完整的模型回答文本
        return completion.choices[0].message.content
        
    except Exception as e:
        print(f"❌ OpenAI SDK 请求异常: {e}")
        return ""
        