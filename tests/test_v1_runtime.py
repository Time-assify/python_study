"""V1.0 Runtime一致性测试

覆盖:
- P0-1 CLI显示新AI Review字段（issues/improvement/knowledge_gaps/next_learning）
- P0-2 统计语义（attempted/completed/total_submissions）
- P0-3 DeepSeek结构化输出schema校验
- P1-3 Task对象保留skills/test_module
"""
import io
import json
import os
import shutil
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from main import cmd_submit  # noqa: E402
from src.agents.code_review_agent import CodeReviewAgent  # noqa: E402
from src.database.db import Database  # noqa: E402
from src.models import EvaluationResult  # noqa: E402
from src.task_manager.task_manager import TaskManager  # noqa: E402


# ---------------- P0-1: CLI显示 ----------------

def _make_result(**overrides):
    base = dict(
        day=1,
        submission_path="submissions/day01/answer.py",
        syntax_valid=True,
        execution_success=True,
        timeout=False,
        tests_total=5,
        tests_passed=5,
        test_score=100.0,
        ai_score=None,
        final_score=100.0,
        ai_review=None,
    )
    base.update(overrides)
    return EvaluationResult(**base)


def _run_submit(result) -> str:
    plat = MagicMock()
    plat.evaluate_submission.return_value = result
    buf = io.StringIO()
    with redirect_stdout(buf):
        cmd_submit(plat, result.day, result.submission_path)
    return buf.getvalue()


class TestCLISubmitDisplay:
    def test_issues_improvement_gaps_nextlearning_shown(self):
        out = _run_submit(_make_result(
            ai_score=80.0,
            ai_review={
                "strengths": ["结构清晰"],
                "issues": ["命名不清晰"],
                "knowledge_gaps": ["Tensor维度"],
                "improvement": ["多写单元测试"],
                "next_learning": ["学习类型注解"],
            },
        ))
        assert "Issues" in out and "命名不清晰" in out
        assert "Improvement" in out and "多写单元测试" in out
        assert "Knowledge Gaps" in out and "Tensor维度" in out
        assert "Next Learning" in out and "学习类型注解" in out

    def test_old_fields_not_displayed(self):
        """bugs/suggestions旧字段即使存在也不应展示"""
        out = _run_submit(_make_result(
            ai_score=70.0,
            ai_review={"bugs": ["x"], "suggestions": ["y"]},
        ))
        assert "\nBugs:" not in out
        assert "\nSuggestions:" not in out

    def test_ai_score_zero_shows_zero(self):
        """AI score=0 必须显示0而不是N/A"""
        out = _run_submit(_make_result(
            ai_score=0.0,
            final_score=70.0,
            ai_review={"strengths": [], "issues": ["很差"]},
        ))
        assert "AI score: 0.0" in out
        assert "AI score: N/A" not in out

    def test_ai_unavailable_no_crash(self):
        """AI不可用：无ai_review时不崩溃，显示N/A"""
        out = _run_submit(_make_result(ai_score=None, ai_review=None))
        assert "AI score: N/A" in out


# ---------------- P0-2: 统计语义 ----------------

class TestStatisticsSemantics:
    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.db = Database(os.path.join(self.tmp, "t.db"))

    def teardown_method(self):
        self.db.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_failed_day_not_completed(self):
        """Day13提交0分：attempted含13，completed不含13"""
        from src.database.db import ProgressRecord
        self.db.save_progress(ProgressRecord(day=13, score=0.0))
        self.db.save_progress(ProgressRecord(day=1, score=80.0))
        stats = self.db.get_learning_statistics()
        assert stats["attempted_days"] == 2
        assert stats["completed_days"] == 1

    def test_total_submissions_uses_new_source(self):
        """total_submissions必须来自submission_history，而非旧submissions表"""
        from src.models import LearningRecord
        for i in range(3):
            self.db.save_submission_history(
                LearningRecord(day=i + 1, task_id=str(i + 1),
                               test_score=70.0, final_score=70.0)
            )
        stats = self.db.get_learning_statistics()
        assert stats["total_submissions"] == 3 == \
            self.db.get_submission_count()


# ---------------- P0-3: schema校验 ----------------

def _agent_with_json(payload):
    mock = MagicMock()
    mock.is_available.return_value = True
    mock.chat.return_value = MagicMock(content=json.dumps(payload))
    mock._extract_json.side_effect = (
        lambda text: json.loads(text) if isinstance(text, str) else None
    )
    return CodeReviewAgent(mock)


VALID = {
    "score": 85,
    "summary": "ok",
    "strengths": ["清晰"],
    "issues": ["命名"],
    "knowledge_gaps": [],
    "improvement": [],
    "next_learning": [],
}


class TestReviewSchemaValidation:
    @pytest.mark.parametrize("bad_payload", [
        {**VALID, "score": 150},
        {**VALID, "score": -5},
        {**VALID, "score": "abc"},
        {**VALID, "score": None},
        {**VALID, "issues": "命名不清晰"},
        {**VALID, "issues": [1, 2]},
        {**VALID, "strengths": "fast"},
        {k: v for k, v in VALID.items() if k != "summary"},
        {k: v for k, v in VALID.items() if k != "knowledge_gaps"},
        {**VALID, "summary": 123},
        "not-a-dict",
    ])
    def test_invalid_schema_rejected(self, bad_payload):
        agent = _agent_with_json(bad_payload)
        result = agent.review(
            day=1, code="x=1", task={}, requirement="",
            pytest_result={"total": 0, "passed": 0, "failed": 0,
                           "errors": 0, "details": []},
        )
        assert result.review_status == "invalid_response"
        assert result.score is None, "非法响应的score必须为None"

    def test_valid_response_passes(self):
        agent = _agent_with_json(VALID)
        result = agent.review(
            day=1, code="x=1", task={}, requirement="",
            pytest_result={"total": 0, "passed": 0, "failed": 0,
                           "errors": 0, "details": []},
        )
        assert result.review_status == "success"
        assert result.score == 85.0


# ---------------- P1-3: Task skills/test_module ----------------

class TestTaskMetadataPreserved:
    def test_day31_task_loads_skills(self):
        manager = TaskManager(tasks_dir=str(ROOT / "tasks"))
        task = manager.get_task(31)
        assert task is not None
        assert "llm.retry" in task.skills
        assert "llm.streaming" in task.skills
        assert task.test_module == "day31_test"

    def test_to_dict_roundtrip_preserves_metadata(self):
        manager = TaskManager(tasks_dir=str(ROOT / "tasks"))
        original = manager.get_task(31)
        data = original.to_dict()
        assert data["test_module"] == "day31_test"
        assert "llm.retry" in data["skills"]

    def test_defaults_when_fields_missing(self):
        from src.task_manager.task_manager import Task
        t = Task(day=99, title="t", goal="g", task="tk",
                 description="d", tests=["test_a"])
        assert t.skills == [] and t.mastery == []
