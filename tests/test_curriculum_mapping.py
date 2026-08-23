"""课程完整性映射检查

验证 tasks/dayXX.json 与 tests/dayXX_test.py 双向一一对应，
且 task JSON 声明的 test_module / skills 字段与实际文件一致。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent


def _load_task(day: int) -> dict:
    return json.loads(
        (ROOT / "tasks" / f"day{day:02d}.json").read_text(encoding="utf-8")
    )


class TestTaskToTestMapping:
    """task JSON 必须指向真实存在的测试模块"""

    def test_test_module_field_matches_file(self):
        for day in range(1, 41):
            task = _load_task(day)
            declared = task.get("test_module")
            assert declared == f"day{day:02d}_test", (
                f"day{day:02d}.json test_module字段错误: {declared!r}"
            )
            assert (ROOT / "tests" / f"{declared}.py").exists(), (
                f"声明模块 {declared} 不存在"
            )


class TestTestToTaskMapping:
    """每个 day 测试必须存在对应 task JSON（反向检查）"""

    def test_every_day_has_both_sides(self):
        for day in range(1, 41):
            assert (ROOT / "tasks" / f"day{day:02d}.json").exists(), (
                f"缺少 tasks/day{day:02d}.json"
            )
            assert (ROOT / "tests" / f"day{day:02d}_test.py").exists(), (
                f"缺少 tests/day{day:02d}_test.py"
            )

    def test_no_orphan_curriculum_files(self):
        """天数集合必须恰好是1..40，不允许孤儿文件"""
        task_days = {int(p.stem[3:5]) for p in (ROOT / "tasks").glob("day??.json")}
        test_days = {int(p.stem[3:5]) for p in (ROOT / "tests").glob("day??_test.py")}
        assert task_days == set(range(1, 41)), f"task天数异常: {sorted(task_days)}"
        assert test_days == set(range(1, 41)), f"test天数异常: {sorted(test_days)}"


class TestSkillTags:
    """skills 标签规范：非空、点分命名空间、已写入测试文件"""

    def test_skills_nonempty_and_namespaced(self):
        # 允许顶层库名(numpy)与点分命名空间(pytorch.cnn)
        pattern = re.compile(r"[a-z_0-9]+(\.[a-z_0-9]+)*")
        for day in range(1, 41):
            skills = _load_task(day).get("skills")
            assert isinstance(skills, list) and skills, f"day{day:02d} skills为空"
            for s in skills:
                assert pattern.fullmatch(s), (
                    f"day{day:02d} 非法skill标签: {s!r}（需点分命名空间）"
                )

    def test_day_tests_carry_skill_marker_on_classes(self):
        marker_on_class = re.compile(
            r"@pytest\.mark\.skill\([^\n]*\)\s*\nclass Test", re.MULTILINE
        )
        for day in range(1, 41):
            src = (ROOT / "tests" / f"day{day:02d}_test.py").read_text(encoding="utf-8")
            assert "@pytest.mark.skill(" in src, (
                f"day{day:02d}_test.py 缺少 @pytest.mark.skill 元数据"
            )
            assert marker_on_class.search(src), (
                f"day{day:02d}_test.py 的skill标记未直接作用于测试类"
            )

    def test_marker_skills_consistent_with_task_json(self):
        """测试文件中的skill标记参数必须与task JSON的skills字段一致"""
        for day in range(1, 41):
            expected = _load_task(day)["skills"]
            src = (ROOT / "tests" / f"day{day:02d}_test.py").read_text(encoding="utf-8")
            first_marker = re.search(r'@pytest\.mark\.skill\(([^)]*)\)', src)
            assert first_marker, f"day{day:02d} 缺少skill标记"
            got = re.findall(r'"([^"]+)"', first_marker.group(1))
            assert sorted(got) == sorted(expected), (
                f"day{day:02d} 标记{got}与JSON声明{expected}不一致"
            )
