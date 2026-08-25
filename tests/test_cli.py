"""P1-1: CLI AI Review字段回归测试

防止ReviewResult字段演进后CLI仍读取旧字段（bugs/suggestions）的回归。
Mock TrainingPlatform.evaluate_submission，不执行pytest/DeepSeek。

P1-5: 增加cmd_task显示格式回归（Required API/Prerequisites/Learn/无Tests泄露）
"""
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from main import cmd_submit, cmd_task, cmd_hint  # noqa: E402
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


# -----------------------------------------------------------------------
# P1-5 / P1-6: cmd_task 显示格式回归
# -----------------------------------------------------------------------

def _capture_task(day: int) -> str:
    from src.core.platform import TrainingPlatform
    plat = TrainingPlatform()
    buf = io.StringIO()
    with redirect_stdout(buf):
        cmd_task(plat, day)
    return buf.getvalue()


def _capture_task_detail(day: int) -> str:
    from src.core.platform import TrainingPlatform
    plat = TrainingPlatform()
    buf = io.StringIO()
    with redirect_stdout(buf):
        cmd_task(plat, day, detail=True)
    return buf.getvalue()


def test_task_contains_required_api():
    """cmd_task day1必须展示 Required API"""
    out = _capture_task(1)
    assert "Required API:" in out, "缺少Required API区块"
    assert "create_project_structure" in out, "签名未出现在Required API中"


def test_task_contains_prerequisites():
    """cmd_task展示 Prerequisites（day1为[]不输出；day5有非空prerequisites）"""
    out = _capture_task(5)  # day5 prerequisites: ["Python字典", "异常处理"]
    assert "Prerequisites" in out


def test_task_contains_learn():
    """--detail视图展示 今天需要学习（P1-2: learn归入详细层）"""
    out = _capture_task_detail(1)
    assert "今天需要学习" in out


def test_task_no_test_names_leaked():
    """cmd_task不得泄露test函数名（系统内部细节），默认与detail均不得泄露"""
    for out in (_capture_task(1), _capture_task_detail(1)):
        assert "test_" not in out, f"不应出现test_函数名，实际输出:\n{out}"


def test_task_contains_hint_levels():
    """--detail视图展示分级提示（P1-2: hints归入详细层）"""
    out = _capture_task_detail(1)
    assert "Hints (卡住时按级查看)" in out or "[L1]" in out
    assert "[L2]" in out or "[L3]" in out


def test_task_default_hides_hints_and_resources():
    """默认视图不显示hints/resources/knowledge points（P1-2分层）"""
    out = _capture_task(2)
    assert "[L" not in out, "默认视图不应显示分级hint"
    assert "Resources:" not in out, "默认视图不应显示resources"
    assert "Knowledge Points:" not in out, "默认视图不应显示knowledge points"
    # 但必须包含核心五要素
    for section in ("Goal:", "Estimated:", "Prerequisites:", "Required API:", "mastery"):
        assert section in out, f"默认视图缺少{section}"
    assert "--detail" in out, "默认视图应引导使用--detail"


def test_task_detail_shows_knowledge_points_resources():
    """--detail视图显示knowledge_points与resources（P1-2）"""
    out = _capture_task_detail(2)
    assert "Knowledge Points:" in out
    assert "python.decorator" in out and "装饰器" in out
    assert "Resources:" in out


# -----------------------------------------------------------------------
# P0-3: hint CLI接口回归
# -----------------------------------------------------------------------

def _capture_hint(day: int, level: int) -> str:
    from src.core.platform import TrainingPlatform
    plat = TrainingPlatform()
    buf = io.StringIO()
    with redirect_stdout(buf):
        cmd_hint(plat, day, level)
    return buf.getvalue()


def test_hint_level1_outputs_only_level1():
    """--level 1只输出L1内容"""
    out = _capture_hint(5, 1)
    assert "[Level 1]" in out or "Level 1" in out
    for line in out.splitlines():
        if line.strip().startswith("- "):
            pass  # 内容行
    assert "[Level 2]" not in out and "[Level 3]" not in out


def test_hint_invalid_level_rejected():
    """level必须是1/2/3，其他值报错不输出提示"""
    out = _capture_hint(5, 4)
    assert "level must be 1, 2 or 3" in out


def test_hint_day5_has_all_three_levels():
    """day05 L1/L2/L3都有内容可取"""
    for lv in (1, 2, 3):
        out = _capture_hint(5, lv)
        assert f"Level {lv}" in out
        assert "-" in out  # 至少一条内容


def test_hint_no_full_answer_leak():
    """hint不得以def/class开头泄露完整实现"""
    for day in (1, 2, 5):
        for lv in (1, 2, 3):
            out = _capture_hint(day, lv)
            for line in out.splitlines():
                stripped = line.strip().lstrip("- ").strip()
                assert not stripped.startswith("def "), \
                    f"day{day} L{lv}疑似完整答案: {stripped[:50]}"
