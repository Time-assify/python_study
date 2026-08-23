"""P1-4: 40天课程完整性检查

防止以后增加Day41任务却忘记增加测试。
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent


class TestCurriculumIntegrity:
    """Day01-Day40: 40个task + 40个day test 全部匹配"""

    def test_all_40_task_files_exist_and_valid(self):
        for day in range(1, 41):
            path = ROOT / "tasks" / f"day{day:02d}.json"
            assert path.exists(), f"缺少任务文件: tasks/day{day:02d}.json"
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                raise AssertionError(f"{path.name} JSON解析失败: {e}")
            for field in ("day", "title", "task"):
                assert field in data, f"{path.name} 缺少必需字段 '{field}'"
            assert int(data["day"]) == day, f"{path.name} 中day={data['day']}与文件名不符"

    def test_all_40_day_test_files_exist(self):
        for day in range(1, 41):
            path = ROOT / "tests" / f"day{day:02d}_test.py"
            assert path.exists(), f"缺少每日测试: tests/day{day:02d}_test.py"

    def test_day_tests_import_answer(self):
        """每个day测试必须import用户提交的answer模块（P1-3原则）"""
        for day in range(1, 41):
            path = ROOT / "tests" / f"day{day:02d}_test.py"
            content = path.read_text(encoding="utf-8")
            assert "import answer" in content, \
                f"{path.name} 必须导入用户的answer模块"

    def test_no_placeholder_tests(self):
        """禁止凑数量占位测试"""
        banned_fragments = (
            "def test_placeholder",
            "assert True  # placeholder",
        )
        for day in range(1, 41):
            path = ROOT / "tests" / f"day{day:02d}_test.py"
            content = path.read_text(encoding="utf-8")
            for frag in banned_fragments:
                assert frag not in content, f"{path.name} 含有占位测试: {frag}"

    def test_day_tests_fail_not_skip_on_missing_api(self):
        """缺少学生实现时应FAIL而不是SKIP：检查_require或pytest.fail机制"""
        for day in range(1, 41):
            path = ROOT / "tests" / f"day{day:02d}_test.py"
            content = path.read_text(encoding="utf-8")
            has_fail_mechanism = ("pytest.fail" in content) or \
                                 ("pytest.importorskip" not in content and "_require" in content)
            assert has_fail_mechanism, f"{path.name} 缺少FAIL机制（必须fail-not-skip）"
