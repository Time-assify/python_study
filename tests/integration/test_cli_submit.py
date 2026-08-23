"""P0-1: CLI提交输出集成测试

Mock EvaluationResult，验证cmd_submit的AI Review展示契约:
- Case A: ai_score=80 → issues/improvement/knowledge_gaps/next_learning全部输出
- Case B: ai_score=0  → 必须显示 "AI score: 0.0"，不能是N/A
- Case C: ai_score=None + fallback review → CLI不崩溃
"""
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).parent.parent.parent
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
        tests_total=4,
        tests_passed=4,
        test_score=100.0,
        ai_score=None,
        final_score=100.0,
        ai_review=None,
    )
    data.update(overrides)
    return EvaluationResult(**data)


def _capture(result: EvaluationResult) -> str:
    platform = MagicMock()
    platform.evaluate_submission.return_value = result
    buf = io.StringIO()
    with redirect_stdout(buf):
        cmd_submit(platform, result.day, result.submission_path)
    return buf.getvalue()


class TestCLISubmitOutput:
    def test_case_a_full_ai_sections(self, capsys):
        """Case A: 五个AI区块全部可见"""
        out = _capture(_result(
            ai_score=80.0,
            final_score=94.0,
            ai_review={
                "strengths": ["函数命名清晰"],
                "issues": ["缺少类型注解"],
                "knowledge_gaps": ["异常处理"],
                "improvement": ["补充docstring"],
                "next_learning": ["学习typing模块"],
            },
        ))
        for header, content in [
            ("Strengths", "函数命名清晰"),
            ("Issues", "缺少类型注解"),
            ("Knowledge Gaps", "异常处理"),
            ("Improvement", "补充docstring"),
            ("Next Learning", "学习typing模块"),
        ]:
            assert header in out, f"缺少区块 {header}"
            assert content in out, f"缺少内容 {content}"

    def test_case_b_zero_score_not_na(self):
        """Case B: ai_score=0 显示0.0而非N/A"""
        out = _capture(_result(
            ai_score=0.0,
            final_score=70.0,
            ai_review={"strengths": [], "issues": ["质量很差"]},
        ))
        assert "AI score: 0.0" in out
        assert "N/A" not in out
        # 空列表区块不显示标题，但非空issues必须显示
        assert "Issues:" in out and "质量很差" in out

    def test_case_c_fallback_no_crash(self):
        """Case C: AI不可用(fallback)时CLI不崩溃"""
        fallback_review = {
            "score": None,
            "summary": "AI审查不可用",
            "review_status": "fallback",
            "strengths": [],
            "issues": ["无法获取AI审查结果"],
            "knowledge_gaps": [],
            "improvement": ["请确保DEEPSEEK_API_KEY环境变量已设置"],
            "next_learning": [],
        }
        out = _capture(_result(
            ai_score=None,
            final_score=100.0,
            ai_review=fallback_review,
        ))
        assert "AI score: N/A" in out
        assert "Final score: 100.0" in out

    def test_empty_review_dict_no_crash(self):
        """边界: ai_review为空dict"""
        out = _capture(_result(ai_score=None, final_score=90.0, ai_review={}))
        assert "Final score: 90.0" in out
