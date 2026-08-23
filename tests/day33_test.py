# Day 33 Tests: RAG检索增强（关键词版，无需向量库）
#
# answer.py 必须实现（接口约定）:
# - chunk_text(text, chunk_size=100, overlap=20) -> list[str]
#   相邻块共享overlap个字符；overlap>=chunk_size抛ValueError
# - cosine_similarity(a, b) -> float    向量点积/模长
# - retrieve(query, docs, k=2) -> list  按词重叠相关性排序取前k
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


@pytest.mark.skipif(np is None, reason="numpy未安装")
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
