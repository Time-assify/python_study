# Day 38 Tests: AI学习导师
#
# answer.py 必须实现（接口约定）:
# - analyze_progress(scores) -> dict  {"average": float, "trend": "improving"|"stable"|"declining"|"insufficient"}
#   trend依据最近3次均值 vs 更早均值，阈值±5分
# - detect_weaknesses(error_counts, threshold=2) -> list  按次数降序过滤薄弱点
#   error_counts为 {错误类型: 次数}
# - recommend_next(error_counts) -> str  最薄弱错误映射到复习主题；空输入返回默认文案
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


@pytest.mark.skill("learning.profile", "recommendation")
class TestAnalyzeProgress:
    def test_average(self):
        analyze = _require("analyze_progress")
        out = analyze([70.0, 80.0, 90.0])
        assert abs(float(out["average"]) - 80.0) < 1e-9

    def test_trend_improving(self):
        analyze = _require("analyze_progress")
        assert analyze([60, 65, 70, 78, 85, 92])["trend"] == "improving"

    def test_trend_declining(self):
        analyze = _require("analyze_progress")
        assert analyze([90, 88, 85, 70, 62, 55])["trend"] == "declining"

    def test_trend_stable(self):
        analyze = _require("analyze_progress")
        assert analyze([80, 81, 79])["trend"] in ("stable",)

    def test_insufficient_data(self):
        """边界条件: 少于3个样本"""
        analyze = _require("analyze_progress")
        out = analyze([80.0])
        assert out["trend"] == "insufficient"

    def test_empty_scores(self):
        analyze = _require("analyze_progress")
        out = analyze([])
        assert float(out.get("average", -1)) == 0.0


@pytest.mark.skill("learning.profile", "recommendation")
class TestDetectWeaknesses:
    def test_threshold_filter_and_order(self):
        detect = _require("detect_weaknesses")
        out = list(detect({"TensorShapeError": 5, "ImportError": 2, "KeyError": 1}, threshold=2))
        assert "KeyError (1次)" not in str(out), "低于阈值的错误不应出现"
        assert len(out) == 2
        # 降序：5次的在前
        first_str = str(out[0])
        assert "TensorShapeError" in first_str or "5" in first_str

    def test_empty_counts(self):
        detect = _require("detect_weaknesses")
        assert list(detect({})) == []


@pytest.mark.skill("learning.profile", "recommendation")
class TestRecommendNext:
    def test_recommends_weakest_topic(self):
        rec = _require("recommend_next")
        topic = str(rec({"TensorShapeError": 6, "SyntaxError": 1}))
        low = topic.lower()
        assert ("tensor" in low) or ("维度" in topic) or ("shape" in low), \
            f"应推荐最薄弱项相关主题: {topic}"

    def test_empty_returns_default(self):
        """边界条件"""
        rec = _require("recommend_next")
        assert isinstance(rec({}), str) and len(rec({})) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
