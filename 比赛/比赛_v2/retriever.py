import numpy as np
from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cosine
import config
from data_utils import load_and_clean_samples

print("⏳ 正在加载向量模型以构建动态检索题库...")
embedder = SentenceTransformer('BAAI/bge-small-zh-v1.5')

# 核心修改点：只读取 config 中指定的题库文件，防止数据泄露
samples = load_and_clean_samples([config.KNOWLEDGE_BASE_FILE])
sample_embeddings = embedder.encode([s['text'] for s in samples])
print(f"题库加载完毕，共 {len(samples)} 条可供检索的样例。")

def retrieve_top_k_shots(query_text, k=3):
    """基于余弦相似度在纯净的题库中检索最相似的句子"""
    query_emb = embedder.encode([query_text])[0]
    distances = [cosine(query_emb, doc_emb) for doc_emb in sample_embeddings]
    top_k_indices = np.argsort(distances)[:k]
    return [samples[i] for i in top_k_indices]