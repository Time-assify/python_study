"""P1-1: 真实判题Smoke测试（合成任务，不泄露课程标准答案）

GitHub Actions绿色不能证明 TestEngine + answer.py + dayXX_test.py 判题链路可用，
因为无answer时day测试会skip。

本文件使用 tests/fixtures/synthetic_grading/ 下的虚拟任务
（safe_divide / parse_numbers / Accumulator，与Day01-Day40完全无关）：

- 运行真实 TestEngine.run_submission()
- 验证 good.score > bad.score 且 bad 至少有1个失败

正式课程只保留契约类检查：
- task-test contract（test_curriculum_mapping.py）
- skill mapping / quality扫描器（test_test_quality*.py）
"""
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.evaluator.test_engine import TestEngine  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "synthetic_grading"
SYNTHETIC_DAY = 90  # 课程范围(1-40)之外，避免与真实day冲突


@pytest.fixture(scope="module")
def engine(tmp_path_factory):
    """准备只含合成测试的隔离tests_dir（day90_test.py）"""
    tests_dir = tmp_path_factory.mktemp("synthetic_tests")
    shutil.copy2(FIXTURES / "synthetic_test.py", tests_dir / "day90_test.py")
    return TestEngine(tests_dir=str(tests_dir), timeout=60)


def _grade(engine, workdir: Path, answer_source: Path):
    """把合成answer复制进隔离目录后走真实TestEngine"""
    env_dir = workdir / "grading"
    env_dir.mkdir(parents=True, exist_ok=True)
    submission = env_dir / "my_answer.py"
    shutil.copy2(answer_source, submission)
    return engine.run_submission(SYNTHETIC_DAY, str(submission))


class TestSyntheticGradingPipeline:
    def test_good_submission_scores_full(self, engine, tmp_path):
        """good实现：全部通过、零error"""
        result = _grade(engine, tmp_path,
                        FIXTURES / "synthetic_answer_good.py")
        assert result.errors == 0, (
            f"good实现不应有error: "
            f"{[t.message[:80] for t in result.test_results if t.status == 'error']}"
        )
        assert result.failed == 0, (
            f"good实现不应有failed: "
            f"{[t.test_name for t in result.test_results if t.status == 'failed']}"
        )
        assert result.score == 100.0, f"good应满分，得到{result.score}"

    def test_bad_submission_has_failures(self, engine, tmp_path):
        """bad实现：至少3个失败（每个虚拟组件各埋一个bug）"""
        result = _grade(engine, tmp_path,
                        FIXTURES / "synthetic_answer_bad.py")
        assert result.failed + result.errors >= 3, (
            f"bad实现应至少失败3项，实际failed={result.failed}"
        )

    def test_engine_distinguishes_good_from_bad(self, engine, tmp_path):
        """核心验收：TestEngine能严格区分good/bad"""
        good = _grade(engine, tmp_path,
                      FIXTURES / "synthetic_answer_good.py")
        bad = _grade(engine, tmp_path,
                     FIXTURES / "synthetic_answer_bad.py")
        assert good.score > bad.score, (
            f"good({good.score:.1f}) 应严格优于 bad({bad.score:.1f})"
        )

    def test_missing_answer_skips_not_crashes(self, engine, tmp_path):
        """无提交时：skip而非崩溃（评测链路的容错行为）"""
        empty = tmp_path / "empty_answer.py"
        empty.write_text("# 故意留空的提交\n", encoding="utf-8")
        result = _grade(engine, tmp_path, empty)
        assert result.errors >= 0 and result.score < 100.0
