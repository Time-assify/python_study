"""Day 33: RAG检索增强生成 - 知识问答系统"""
import json
from typing import List, Dict, Tuple


class SimpleEmbedding:
    """简单词嵌入"""

    def __init__(self, embed_dim=64):
        import random
        self.embed_dim = embed_dim
        self.embeddings = {}
        words = ["python", "machine", "learning", "deep", "neural",
                 "network", "data", "model", "train", "code"]
        for w in words:
            self.embeddings[w] = [random.random() for _ in range(embed_dim)]

    def get_embedding(self, text):
        words = text.lower().split()
        if not words:
            return [0.0] * self.embed_dim
        emb = [0.0] * self.embed_dim
        count = 0
        for word in words:
            if word in self.embeddings:
                emb = [e + self.embeddings[word][i] for i, e in enumerate(emb)]
                count += 1
        if count > 0:
            emb = [e / count for e in emb]
        return emb


class VectorStore:
    """向量存储"""

    def __init__(self):
        self.vectors = []
        self.embedding_model = SimpleEmbedding()

    def add(self, doc_id, text, metadata=None):
        embedding = self.embedding_model.get_embedding(text)
        self.vectors.append((doc_id, embedding, {"text": text, **(metadata or {})}))

    def search(self, query, top_k=3):
        query_emb = self.embedding_model.get_embedding(query)
        results = []
        for doc_id, emb, meta in self.vectors:
            dot = sum(a * b for a, b in zip(query_emb, emb))
            norm1 = sum(a ** 2 for a in query_emb) ** 0.5
            norm2 = sum(b ** 2 for b in emb) ** 0.5
            sim = dot / (norm1 * norm2) if norm1 * norm2 > 0 else 0
            results.append((doc_id, sim, meta))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]


class DocumentProcessor:
    """文档处理器"""

    def __init__(self, chunk_size=200):
        self.chunk_size = chunk_size

    def process(self, text, metadata=None):
        chunks = []
        words = text.split()
        current = []
        for word in words:
            current.append(word)
            if len(" ".join(current)) >= self.chunk_size:
                chunks.append({
                    "text": " ".join(current),
                    "metadata": metadata or {}
                })
                current = []
        if current:
            chunks.append({"text": " ".join(current), "metadata": metadata or {}})
        return chunks


class RAGSystem:
    """RAG系统"""

    def __init__(self):
        self.vector_store = VectorStore()
        self.processor = DocumentProcessor()

    def add_document(self, text, doc_id=None):
        doc_id = doc_id or f"doc_{len(self.vector_store.vectors)}"
        chunks = self.processor.process(text, {"doc_id": doc_id})
        for i, chunk in enumerate(chunks):
            self.vector_store.add(f"{doc_id}_{i}", chunk["text"], chunk["metadata"])

    def query(self, question, top_k=3):
        results = self.vector_store.search(question, top_k)
        context = "\n".join([r[2]["text"] for r in results])
        return {"context": context, "sources": [(r[0], r[1]) for r in results]}


if __name__ == "__main__":
    print("RAG系统示例\n")

    rag = RAGSystem()
    rag.add_document("Python is a programming language for AI and ML.")
    rag.add_document("Deep learning uses neural networks with many layers.")
    rag.add_document("PyTorch is a deep learning framework by Facebook.")

    result = rag.query("What is Python?")
    print(f"Query: What is Python?")
    print(f"Context: {result['context']}")
    print(f"Sources: {result['sources']}")