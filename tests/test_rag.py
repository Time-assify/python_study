# RAG Knowledge Base Tests
import pytest
import os
import tempfile
import shutil
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rag.knowledge_base import KnowledgeBase, Document, Chunk


class TestKnowledgeBase:
    """知识库测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.test_dir = tempfile.mkdtemp()
        self.kb = KnowledgeBase(persist_dir=self.test_dir)
    
    def teardown_method(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_init(self):
        """测试初始化"""
        kb = KnowledgeBase(persist_dir=self.test_dir)
        assert kb is not None
        assert len(kb.documents) == 0
        assert len(kb.chunks) == 0
    
    def test_add_document(self):
        """测试添加文档"""
        doc_id = self.kb.add_document(
            content="This is a test document. " * 50,
            metadata={"source": "test"}
        )
        
        assert doc_id is not None
        assert len(self.kb.documents) == 1
        assert len(self.kb.chunks) > 0
    
    def test_add_text(self):
        """测试添加文本"""
        doc_id = self.kb.add_text(
            text="Hello world. This is a test.",
            source="test_source"
        )
        
        assert doc_id is not None
        assert len(self.kb.documents) == 1
    
    def test_add_file(self):
        """测试添加文件"""
        # 创建临时文件
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("This is test file content. " * 20)
        
        doc_id = self.kb.add_file(test_file)
        assert doc_id is not None
    
    def test_search(self):
        """测试搜索"""
        self.kb.add_text("Python is a programming language", source="test1")
        self.kb.add_text("Java is also a programming language", source="test2")
        self.kb.add_text("Cats are cute animals", source="test3")
        
        results = self.kb.search("Python programming", top_k=2)
        
        assert len(results) > 0
        assert results[0]["score"] > 0
    
    def test_get_document(self):
        """测试获取文档"""
        doc_id = self.kb.add_text("Test content", source="test")
        
        doc = self.kb.get_document(doc_id)
        assert doc is not None
        assert doc.id == doc_id
        assert doc.content == "Test content"
    
    def test_get_chunks_by_document(self):
        """测试获取文档块"""
        doc_id = self.kb.add_text("Test content", source="test")
        
        chunks = self.kb.get_chunks_by_document(doc_id)
        assert len(chunks) > 0
        assert chunks[0].document_id == doc_id
    
    def test_delete_document(self):
        """测试删除文档"""
        doc_id = self.kb.add_text("Test content", source="test")
        
        initial_count = len(self.kb.documents)
        result = self.kb.delete_document(doc_id)
        
        assert result is True
        assert len(self.kb.documents) == initial_count - 1
    
    def test_statistics(self):
        """测试统计信息"""
        self.kb.add_text("Test 1", source="test1")
        self.kb.add_text("Test 2", source="test2")
        
        stats = self.kb.get_statistics()
        
        assert stats["total_documents"] == 2
        assert stats["total_chunks"] > 0
        assert stats["average_chunk_size"] > 0
    
    def test_persistence(self):
        """测试持久化"""
        self.kb.add_text("Persistent content", source="test")
        
        # 创建新的知识库实例
        kb2 = KnowledgeBase(persist_dir=self.test_dir)
        
        assert len(kb2.documents) == 1
        assert len(kb2.chunks) > 0
    
    def test_clear(self):
        """测试清空"""
        self.kb.add_text("Test 1", source="test1")
        self.kb.add_text("Test 2", source="test2")
        
        self.kb.clear()
        
        assert len(self.kb.documents) == 0
        assert len(self.kb.chunks) == 0
    
    def test_chunking(self):
        """测试分块"""
        long_text = "This is a sentence. " * 100
        
        doc_id = self.kb.add_document(
            content=long_text,
            chunk_size=200,
            chunk_overlap=20
        )
        
        chunks = self.kb.get_chunks_by_document(doc_id)
        assert len(chunks) > 1


class TestDocument:
    """文档测试"""
    
    def test_document_creation(self):
        """测试文档创建"""
        doc = Document(
            id="test_doc",
            content="Test content",
            metadata={"source": "test"}
        )
        
        assert doc.id == "test_doc"
        assert doc.content == "Test content"
        assert doc.metadata["source"] == "test"
    
    def test_document_default_metadata(self):
        """测试默认元数据"""
        doc = Document(id="test_doc", content="Test content")
        assert doc.metadata == {}


class TestChunk:
    """块测试"""
    
    def test_chunk_creation(self):
        """测试块创建"""
        chunk = Chunk(
            id="test_chunk",
            document_id="test_doc",
            content="Test content",
            index=0,
            metadata={"source": "test"}
        )
        
        assert chunk.id == "test_chunk"
        assert chunk.document_id == "test_doc"
        assert chunk.index == 0
    
    def test_chunk_default_metadata(self):
        """测试默认元数据"""
        chunk = Chunk(
            id="test_chunk",
            document_id="test_doc",
            content="Test content",
            index=0
        )
        assert chunk.metadata == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])