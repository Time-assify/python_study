"""P0-3: 完整Pipeline集成测试 - 真实TrainingPlatform.evaluate_submission()

P0-1(安全收口): 不再包含任何Day01-Day40真实课程答案。
使用 tests/fixtures/synthetic_pipeline/ 的合成任务(day90):
    safe_divide / normalize_name / Accumulator

覆盖:
- Case A: 正确提交（全链路落库）
- Case B: 逻辑错误（LogicError分类+error_statistics更新）
- Case C: 语法错误（final_score=0）
- Case D: 死循环（timeout=True传播到EvaluationResult）
- Case E: DeepSeek不可用（ai_score=None, final==test_score）
- Case F: 历史反馈（第二次Prompt包含第一次错误）
"""
import json
import shutil
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import src.database as database_module  # noqa: E402
import src.llm as llm_module  # noqa: E402
from src.database.db import Database  # noqa: E402
from src.core.platform import TrainingPlatform  # noqa: E402
from src.evaluator.test_engine import TestEngine  # noqa: E402
from src.models import LearningRecord  # noqa: E402

FIXTURES = Path(__file__).parent.parent.parent / \
    "tests" / "fixtures" / "synthetic_pipeline"

SYNTHETIC_DAY = 90  # 课程范围(1-40)之外


class FakeLLM:
    """可用的Mock LLM"""

    def __init__(self):
        self.chat_calls = []

    def is_available(self):
        return True

    def chat(self, messages, model=None, temperature=0.7, max_tokens=2000):
        self.chat_calls.append(messages)

        class R:
            content = json.dumps({
                "score": 85,
                "summary": "质量不错",
                "strengths": ["结构清晰"],
                "issues": [],
                "knowledge_gaps": [],
                "improvement": ["继续"],
                "next_learning": [],
            })

        return R()

    @staticmethod
    def _extract_json(content):
        try:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(content[start:end])
        except (json.JSONDecodeError, ValueError):
            pass
        return None


@pytest.fixture()
def make_platform(tmp_path, monkeypatch):
    """构造带临时DB、Mock LLM、合成测试目录的真实TrainingPlatform"""

    def _make(llm_available=True):
        db = Database(str(tmp_path / f"db_{id(_make)}.sqlite"))
        monkeypatch.setattr(database_module, "Database", lambda *a, **k: db)

        if llm_available:
            fake_llm = FakeLLM()
        else:
            fake_llm = MagicMock()
            fake_llm.is_available.return_value = False
        monkeypatch.setattr(llm_module, "DeepSeekClient", lambda *a, **k: fake_llm)

        plat = TrainingPlatform()
        plat.database = db

        # 合成测试环境: pipeline_synthetic_cases.py -> <tmp>/day90_test.py
        tests_dir = tmp_path / f"syn_tests_{id(_make)}"
        tests_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(FIXTURES / "pipeline_synthetic_cases.py",
                     tests_dir / "day90_test.py")
        plat.test_engine = TestEngine(tests_dir=str(tests_dir), timeout=30)

        # day90无task JSON → 桩掉TaskManager避免ValueError
        plat.task_manager = MagicMock()
        plat.task_manager.get_task.return_value = None

        return plat, fake_llm, db

    return _make


def _write_answer(tmp_path, code):
    """每个测试有独立tmp_path，直接平铺写入"""
    p = tmp_path / "answer.py"
    p.write_text(code, encoding="utf-8")
    return p


def _load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class TestCaseACorrectSubmission:
    def test_full_pipeline_correct(self, make_platform, tmp_path):
        """Case A: 正确提交→全链路验证"""
        plat, _llm, db = make_platform()
        ans = _write_answer(tmp_path, _load_fixture("synthetic_answer_good.py"))

        result = plat.evaluate_submission(SYNTHETIC_DAY, ans)

        assert result.syntax_valid is True
        assert result.execution_success is True
        assert result.test_score == 100.0
        assert result.final_score >= 100.0 * 0.7  # AI加权后仍很高

        # submission_history写入
        subs = db.get_submission_history(day=SYNTHETIC_DAY)
        assert len(subs) == 1
        assert subs[0]["test_score"] == 100.0

        # review_history写入
        reviews = db.get_review_history(day=SYNTHETIC_DAY)
        assert len(reviews) == 1
        assert reviews[0]["review_result"].get("score") == 85

        # StudentProfile可读取
        profile = db.update_profile()
        assert profile["total_submissions"] >= 1


class TestCaseBLogicError:
    def test_logic_error_classified(self, make_platform, tmp_path):
        """Case B: 逻辑错误→LogicError分类+error_statistics更新"""
        plat, _llm, db = make_platform()
        ans = _write_answer(tmp_path, _load_fixture("synthetic_answer_bad.py"))

        result = plat.evaluate_submission(SYNTHETIC_DAY, ans)

        assert result.test_score < 100.0, "错误实现不应满分"

        stats = db.get_error_statistics()
        assert stats.get("LogicError", 0) >= 1, (
            f"AssertionError应被分类为LogicError: {stats}"
        )

        profile = db.update_profile()
        assert "LogicError" in profile["error_statistics"]

    def test_wrong_answer_recorded_with_errors(self, make_platform, tmp_path):
        plat, _llm, db = make_platform()
        ans = _write_answer(tmp_path, _load_fixture("synthetic_answer_bad.py"))
        plat.evaluate_submission(SYNTHETIC_DAY, ans)
        rec = db.get_submission_history(day=SYNTHETIC_DAY)[0]
        assert len(rec["errors"]) >= 1
        assert any(e["error_type"] == "LogicError" for e in rec["errors"])


class TestCaseCSyntaxError:
    def test_syntax_error_zero_score(self, make_platform, tmp_path):
        """Case C: 语法错误→syntax_valid=False, final_score=0"""
        plat, _llm, _db = make_platform()
        ans = _write_answer(tmp_path, "def broken(:\n    pass\n")

        result = plat.evaluate_submission(SYNTHETIC_DAY, ans)

        assert result.syntax_valid is False
        assert result.final_score == 0.0


class TestCaseDInfiniteLoop:
    def test_timeout_propagates(self, make_platform, tmp_path):
        """Case D: 死循环→timeout=True且final_score=0"""
        plat, _llm, _db = make_platform()
        plat.code_executor.timeout = 2   # 缩短执行检查超时
        plat.test_engine.timeout = 4     # 缩短pytest超时
        ans = _write_answer(tmp_path, "while True:\n    pass\n")

        result = plat.evaluate_submission(SYNTHETIC_DAY, ans)

        # 必须显式检查timeout字段传播（不能只查score）
        assert result.timeout is True, "TestEngine超时必须传播到EvaluationResult.timeout"
        assert result.final_score == 0.0


class TestCaseELLUnavailable:
    def test_ai_off_does_not_affect_pytest(self, make_platform, tmp_path):
        """Case E: AI不可用→ai_score=None, final==test_score"""
        plat, _llm, db = make_platform(llm_available=False)
        ans = _write_answer(tmp_path, _load_fixture("synthetic_answer_good.py"))

        result = plat.evaluate_submission(SYNTHETIC_DAY, ans)

        assert result.ai_score is None
        assert result.final_score == result.test_score == 100.0

        # fallback的70分不得入库参与评分
        reviews = db.get_review_history(day=SYNTHETIC_DAY)
        assert reviews[0]["review_result"]["score"] is None


class TestCaseFHistoryFeedback:
    def test_second_prompt_contains_first_error(self, make_platform, tmp_path):
        """Case F: 第一次TensorShapeError→第二次Prompt可见（含同日重提交）"""
        plat, fake_llm, db = make_platform()

        # 模拟第一次提交产生的真实数据库记录（走真实save路径）
        seed = LearningRecord(
            day=SYNTHETIC_DAY,
            task_id=str(SYNTHETIC_DAY),
            submission_path=str(tmp_path / "first.py"),
            test_score=40.0,
            ai_score=None,
            final_score=40.0,
            errors=[{
                "test_name": "test_matmul",
                "message": "RuntimeError: mat1 and mat2 shapes cannot be multiplied",
                "error_type": "TensorShapeError",
            }],
        )
        assert db.save_submission_history(seed) > 0

        ans = _write_answer(tmp_path, _load_fixture("synthetic_answer_good.py"))
        plat.evaluate_submission(SYNTHETIC_DAY, ans)  # 第二次提交（同day）

        assert len(fake_llm.chat_calls) >= 1
        user_prompt = fake_llm.chat_calls[0][1]["content"]
        assert "TensorShapeError" in user_prompt, (
            "第二次Review的Prompt必须包含第一次的TensorShapeError:\n"
            + user_prompt[:800]
        )
