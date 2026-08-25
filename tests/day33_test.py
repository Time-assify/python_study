# Day 33 Tests: RAG检索增强（关键词版，无需向量库）
#
# answer.py 必须实现（接口约定）:
# - chunk_text(text, chunk_size=100, overlap=20) -> list[str]
#   相邻块共享overlap个字符；overlap>=chunk_size抛ValueError
# - cosine_similarity(a, b) -> float    向量点积/模长
# - retrieve(query, docs, k=2) -> list  按词重叠相关性排序取前k
# - build_rag_prompt(question, chunks) -> str  组装"仅依据资料回答"的prompt; 空资料含兜底说明
import pytest

try:
    import answer
except ModuleNotFoundError as e:
    if getattr(e, "name", "") == "answer":
        answer = None
    else:
        raise
except Exception:
    raise

try:
    import numpy as np
except ImportError:
    np = None


def test_answer_module_imports():
    """answer exists -> import errors are FAIL; only skip when repo has no submission"""
    if answer is None:
        pytest.skip("no answer.py under review (TestEngine injects it during real grading)")


def _require(name):
    if answer is None:
        pytest.skip("no answer.py under review")
    fn = getattr(answer, name, None)
    if fn is None:
        pytest.fail(f"必须实现 {name}()")
    return fn


@pytest.mark.skill("rag.chunking", "rag.retrieval")
class TestChunking:
    def test_chunks_with_overlap(self):
        chunk = _require("chunk_text")
        text = "0123456789" * 3  # 30字符
        parts = chunk(text, chunk_size=10, overlap=4)
        assert len(parts) >= 2
        # 相邻块应有overlap个字符重叠
        assert parts[1][:4] == text[6:10], "相邻块必须共享overlap前缀"

    def test_overlap_ge_chunk_raises(self):
        """错误处理"""
        chunk = _require("chunk_text")
        with pytest.raises(ValueError):
            chunk("abcdef", chunk_size=5, overlap=5)

    def test_short_text_single_chunk(self):
        """边界条件: 短文本单块"""
        chunk = _require("chunk_text")
        assert chunk("short", 100) == ["short"]


@pytest.mark.skipif(np is None, reason="numpy未安装（环境问题）")
@pytest.mark.skill("rag.chunking", "rag.retrieval")
class TestCosineSimilarity:
    def _require_cos(self):
        return _require("cosine_similarity")

    def test_identical_vectors(self):
        cos = self._require_cos()
        v = [1.0, 2.0, 3.0]
        assert abs(float(cos(v, v)) - 1.0) < 1e-6

    def test_orthogonal_zero(self):
        cos = self._require_cos()
        assert abs(float(cos([1, 0], [0, 1]))) < 1e-9

    def test_opposite_negative(self):
        cos = self._require_cos()
        assert float(cos([1, 0], [-1, 0])) < -0.999


@pytest.mark.skill("rag.chunking", "rag.retrieval")
class TestRetrieve:
    def test_most_relevant_first(self):
        retrieve = _require("retrieve")
        docs = [
            "今天天气不错适合散步",
            "PyTorch tensor操作教程",
            "深度学习中的tensor维度变换技巧",
        ]
        out = retrieve("tensor 维度", docs, k=2)
        first = out[0] if not isinstance(out[0], dict) else str(out[0])
        assert "tensor" in str(first).lower() or "维度" in str(first), f"排序失败: {out}"

    def test_k_limits_results(self):
        retrieve = _require("retrieve")
        docs = ["a b", "c d", "e f"]
        assert len(list(retrieve("任意", docs, k=2))) == 2

    def test_k_exceeds_docs(self):
        """边界条件"""
        retrieve = _require("retrieve")
        out = list(retrieve("x", ["only one"], k=5))
        assert len(out) == 1


@pytest.mark.skill("rag.retrieval", "llm.client")
class TestRAGGeneration:
    """mini-RAG最后一环: 检索结果 → 可交给LLM的生成prompt"""

    def test_prompt_contains_question_and_context(self):
        fn = _require("build_rag_prompt")
        chunks = ["PyTorch张量是多元数组。", "DataLoader负责批处理。"]
        prompt = fn("什么是Tensor?", chunks)
        assert isinstance(prompt, str) and prompt.strip()
        assert "什么是Tensor?" in prompt, "用户问题必须进入prompt"
        assert "张量是多元数组" in prompt, "检索到的资料必须进入prompt"
        assert ("资料" in prompt) or ("context" in prompt.lower()), \
            "应指示模型仅依据资料作答"

    def test_empty_retrieval_fallback(self):
        """边界: 无检索结果时prompt仍应良构(含兜底说明)"""
        fn = _require("build_rag_prompt")
        prompt = fn("什么是Tensor?", [])
        assert isinstance(prompt, str) and prompt.strip()
        assert "什么是Tensor?" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
