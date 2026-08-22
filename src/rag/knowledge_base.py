"""RAG知识库模块"""
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class Document:
    """文档数据类"""
    id: str
    content: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Chunk:
    """文档块数据类"""
    id: str
    document_id: str
    content: str
    index: int
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class KnowledgeBase:
    """RAG知识库
    
    支持文档加载、分块、检索等功能。
    """
    
    def __init__(self, persist_dir: str = "data/knowledge_base"):
        """初始化知识库
        
        Args:
            persist_dir: 持久化目录
        """
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        self.documents: Dict[str, Document] = {}
        self.chunks: List[Chunk] = []
        
        # 加载已有的数据
        self._load_from_disk()
    
    def _load_from_disk(self):
        """从磁盘加载数据"""
        docs_file = self.persist_dir / "documents.json"
        chunks_file = self.persist_dir / "chunks.json"
        
        if docs_file.exists():
            with open(docs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for doc_id, doc_data in data.items():
                    self.documents[doc_id] = Document(**doc_data)
        
        if chunks_file.exists():
            with open(chunks_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for chunk_data in data:
                    self.chunks.append(Chunk(**chunk_data))
    
    def _save_to_disk(self):
        """保存数据到磁盘"""
        # 保存文档
        docs_data = {}
        for doc_id, doc in self.documents.items():
            docs_data[doc_id] = {
                "id": doc.id,
                "content": doc.content,
                "metadata": doc.metadata
            }
        
        with open(self.persist_dir / "documents.json", 'w', encoding='utf-8') as f:
            json.dump(docs_data, f, ensure_ascii=False, indent=2)
        
        # 保存块
        chunks_data = []
        for chunk in self.chunks:
            chunks_data.append({
                "id": chunk.id,
                "document_id": chunk.document_id,
                "content": chunk.content,
                "index": chunk.index,
                "metadata": chunk.metadata
            })
        
        with open(self.persist_dir / "chunks.json", 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, ensure_ascii=False, indent=2)
    
    def add_document(self, 
                    content: str, 
                    doc_id: str = None,
                    metadata: Dict[str, Any] = None,
                    chunk_size: int = 500,
                    chunk_overlap: int = 50) -> str:
        """添加文档
        
        Args:
            content: 文档内容
            doc_id: 文档ID（可选）
            metadata: 元数据
            chunk_size: 块大小
            chunk_overlap: 块重叠大小
            
        Returns:
            文档ID
        """
        # 生成文档ID
        if doc_id is None:
            doc_id = f"doc_{len(self.documents) + 1}"
        
        # 创建文档
        doc = Document(
            id=doc_id,
            content=content,
            metadata=metadata or {}
        )
        self.documents[doc_id] = doc
        
        # 分块
        doc_chunks = self._split_text(content, chunk_size, chunk_overlap)
        
        for i, chunk_content in enumerate(doc_chunks):
            chunk = Chunk(
                id=f"{doc_id}_chunk_{i}",
                document_id=doc_id,
                content=chunk_content,
                index=i,
                metadata={"source": doc_id}
            )
            self.chunks.append(chunk)
        
        # 保存到磁盘
        self._save_to_disk()
        
        return doc_id
    
    def add_text(self, 
                text: str, 
                source: str = "unknown",
                chunk_size: int = 500) -> str:
        """添加文本
        
        Args:
            text: 文本内容
            source: 来源
            chunk_size: 块大小
            
        Returns:
            文档ID
        """
        return self.add_document(
            content=text,
            metadata={"source": source},
            chunk_size=chunk_size
        )
    
    def add_file(self, file_path: str, chunk_size: int = 500) -> str:
        """添加文件
        
        Args:
            file_path: 文件路径
            chunk_size: 块大小
            
        Returns:
            文档ID
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 读取文件内容
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.add_document(
            content=content,
            metadata={"source": str(path), "filename": path.name},
            chunk_size=chunk_size
        )
    
    def _split_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """将文本分割成块
        
        Args:
            text: 文本内容
            chunk_size: 块大小
            overlap: 重叠大小
            
        Returns:
            文本块列表
        """
        chunks = []
        
        # 按段落分割
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # 如果当前块加上新段落超过大小限制
            if len(current_chunk) + len(paragraph) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # 如果单个段落超过块大小，进一步分割
                if len(paragraph) > chunk_size:
                    words = paragraph.split()
                    current_chunk = ""
                    for word in words:
                        if len(current_chunk) + len(word) + 1 > chunk_size:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = word
                        else:
                            current_chunk += " " + word if current_chunk else word
                else:
                    current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text]
    
    def search(self, 
              query: str, 
              top_k: int = 5,
              min_score: float = 0.0) -> List[Dict[str, Any]]:
        """搜索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回的最大结果数
            min_score: 最小相似度分数
            
        Returns:
            搜索结果列表
        """
        results = []
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for chunk in self.chunks:
            # 计算简单的文本相似度
            chunk_lower = chunk.content.lower()
            chunk_words = set(chunk_lower.split())
            
            # 计算词汇重叠度
            if not query_words:
                score = 0
            else:
                overlap = len(query_words & chunk_words)
                score = overlap / len(query_words)
            
            # 检查查询是否在块中
            if query_lower in chunk_lower:
                score += 0.5
            
            if score >= min_score:
                results.append({
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "content": chunk.content,
                    "score": score,
                    "metadata": chunk.metadata
                })
        
        # 按分数排序
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:top_k]
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """获取文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            Document对象
        """
        return self.documents.get(doc_id)
    
    def get_chunks_by_document(self, doc_id: str) -> List[Chunk]:
        """获取文档的所有块
        
        Args:
            doc_id: 文档ID
            
        Returns:
            Chunk列表
        """
        return [chunk for chunk in self.chunks if chunk.document_id == doc_id]
    
    def delete_document(self, doc_id: str) -> bool:
        """删除文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            是否删除成功
        """
        if doc_id not in self.documents:
            return False
        
        # 删除文档
        del self.documents[doc_id]
        
        # 删除相关的块
        self.chunks = [chunk for chunk in self.chunks if chunk.document_id != doc_id]
        
        # 保存到磁盘
        self._save_to_disk()
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        total_chunks = len(self.chunks)
        total_docs = len(self.documents)
        
        avg_chunk_size = 0
        if total_chunks > 0:
            avg_chunk_size = sum(len(c.content) for c in self.chunks) / total_chunks
        
        return {
            "total_documents": total_docs,
            "total_chunks": total_chunks,
            "average_chunk_size": round(avg_chunk_size, 2)
        }
    
    def clear(self):
        """清空知识库"""
        self.documents.clear()
        self.chunks.clear()
        self._save_to_disk()