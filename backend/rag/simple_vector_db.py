"""
简单向量数据库 - 替代Chroma的轻量级实现
"""
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple
import os


class SimpleVectorDB:
    """简单向量数据库"""

    def __init__(self, db_path: str = None, model_path: str = "../models/bge-large-zh"):
        self.chunks = []
        self.embeddings = None
        self.model_path = model_path
        self.model = None

        if db_path and os.path.exists(db_path):
            self.load(db_path)

    def load(self, db_path: str):
        """加载向量库"""
        with open(db_path, 'rb') as f:
            data = pickle.load(f)
        self.chunks = data["chunks"]
        self.embeddings = data["embeddings"]
        print(f"[加载] 向量库: {db_path}")
        print(f"  - 文本块数量: {len(self.chunks)}")
        print(f"  - 向量维度: {self.embeddings.shape[1]}")

    def _get_model(self):
        """懒加载模型"""
        if self.model is None:
            print(f"[加载] 模型: {self.model_path}")
            self.model = SentenceTransformer(self.model_path)
        return self.model

    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """计算余弦相似度"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def query(self, query_text: str, top_k: int = 3) -> List[Dict]:
        """
        查询向量库

        Args:
            query_text: 查询文本
            top_k: 返回结果数量

        Returns:
            包含文本和相似度的结果列表
        """
        if self.embeddings is None:
            raise ValueError("向量库未加载")

        # 生成查询向量
        model = self._get_model()
        query_embedding = model.encode([query_text])[0]

        # 计算相似度
        similarities = [
            self.cosine_similarity(query_embedding, emb)
            for emb in self.embeddings
        ]

        # 获取Top K
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        results = []
        for idx in top_indices:
            results.append({
                "text": self.chunks[idx],
                "score": float(similarities[idx]),
                "index": int(idx)
            })

        return results

    def get_context(self, query_text: str, top_k: int = 3, max_length: int = 1500) -> str:
        """
        获取查询相关的上下文文本（用于RAG）

        Args:
            query_text: 查询文本
            top_k: 检索片段数量
            max_length: 最大上下文长度

        Returns:
            拼接的上下文文本
        """
        results = self.query(query_text, top_k=top_k)

        context_parts = []
        current_length = 0

        for r in results:
            text = r["text"]
            if current_length + len(text) > max_length:
                remaining = max_length - current_length
                context_parts.append(text[:remaining])
                break
            context_parts.append(text)
            current_length += len(text)

        return "\n\n".join(context_parts)


if __name__ == "__main__":
    # 测试
    import sys

    if len(sys.argv) < 2:
        print("用法: python simple_vector_db.py <向量库路径>")
        sys.exit(1)

    db_path = sys.argv[1]
    db = SimpleVectorDB(db_path)

    print("\n输入查询内容 (输入 'quit' 退出):")
    while True:
        query = input("> ").strip()
        if query.lower() == 'quit':
            break
        if not query:
            continue

        results = db.query(query, top_k=3)
        print(f"\n查询: {query}")
        print("-" * 50)
        for i, r in enumerate(results, 1):
            print(f"\n结果 {i} (相似度: {r['score']:.4f}):")
            print(r['text'][:300] + "..." if len(r['text']) > 300 else r['text'])
        print("\n" + "=" * 50)
