"""P1-1: CLI AI Review字段回归测试

防止ReviewResult字段演进后CLI仍读取旧字段（bugs/suggestions）的回归。
Mock TrainingPlatform.evaluate_submission，不执行pytest/DeepSeek。
"""
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from main import cmd_submit  # noqa: E402
from src.models import EvaluationResult  # noqa: E402


def _result(**overrides) -> EvaluationResult:
    data = dict(
        day=1,
        submission_path="submissions/day01/answer.py",
        syntax_valid=True,
        execution_success=True,
        timeout=False,
        tests_total=1,
        tests_passed=1,
        test_score=100.0,
        ai_score=None,
        final_score=100.0,
        ai_review=None,
    )
    data.update(overrides)
    return EvaluationResult(**data)


def _capture(result) -> str:
    plat = MagicMock()
    plat.evaluate_submission.return_value = result
    buf = io.StringIO()
    with redirect_stdout(buf):
        cmd_submit(plat, result.day, result.submission_path)
    return buf.getvalue()


def test_case1_zero_score_shows_zero():
    """ai_score=0 → 'AI score: 0.0'，不得显示N/A"""
    out = _capture(_result(ai_score=0.0, final_score=70.0))
    assert "AI score: 0.0" in out
    assert "N/A" not in out


def test_case2_all_five_sections():
    """strengths/issues/knowledge_gaps/improvement/next_learning A-E全输出"""
    review = {
        "strengths": ["A"],
        "issues": ["B"],
        "knowledge_gaps": ["C"],
        "improvement": ["D"],
        "next_learning": ["E"],
    }
    out = _capture(_result(ai_score=80.0, final_score=94.0, ai_review=review))
    for header, content in [
        ("Strengths", "A"),
        ("Issues", "B"),
        ("Knowledge Gaps", "C"),
        ("Improvement", "D"),
        ("Next Learning", "E"),
    ]:
        assert header in out and content in out


def test_case3_none_no_crash():
    """ai_score=None + 无review → 不崩溃，显示N/A"""
    out = _capture(_result(ai_score=None, final_score=100.0, ai_review=None))
    assert "AI score: N/A" in out
    assert "Final score: 100.0" in out


def test_legacy_fields_ignored():
    """回归保护: 即使review里混入旧字段bugs/suggestions也不展示"""
    review = {"bugs": ["old-bug"], "suggestions": ["old-sug"],
              "issues": ["new-issue"]}
    out = _capture(_result(ai_score=60.0, final_score=88.0, ai_review=review))
    assert "\nBugs:" not in out
    assert "\nSuggestions:" not in out
    assert "new-issue" in out
