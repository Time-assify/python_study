"""课程完整性映射检查

验证:
1. tasks/dayXX.json 与 tests/dayXX_test.py 双向一一对应
2. task JSON 的 test_module / skills 字段与实际文件一致
3. P0-1: task["tests"] 中每个ID必须映射到真实pytest函数（AST收集）
4. P1-4: 每个测试类的skill标记必须是task skills子集，
   且声明的skills必须至少被一个类覆盖（AST解析全部标记）
"""
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent


def _load_task(day: int) -> dict:
    return json.loads(
        (ROOT / "tasks" / f"day{day:02d}.json").read_text(encoding="utf-8")
    )


def _collect_test_names(tree) -> set:
    """AST收集模块级与类内所有 test_* 函数名"""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and \
                node.name.startswith("test_"):
            names.add(node.name)
    return names


def _class_skill_markers(path: Path) -> dict:
    """P1-4: AST解析全部 @pytest.mark.skill(...) 类装饰器

    返回 {类名: set(skill字符串)}
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    result = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        skills = set()
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            func = dec.func
            # 匹配 pytest.mark.skill(...)
            parts = []
            while isinstance(func, ast.Attribute):
                parts.append(func.attr)
                func = func.value
            if isinstance(func, ast.Name):
                parts.append(func.id)
            # parts为自内向外: [skill, mark, pytest] → 反转后比对
            if len(parts) >= 3 and \
                    list(reversed(parts))[-3:] == ["pytest", "mark", "skill"]:
                for arg in dec.args:
                    if isinstance(arg, ast.Constant) and \
                            isinstance(arg.value, str):
                        skills.add(arg.value)
        if skills:
            result[node.name] = skills
    return result


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


class TestDeclaredTestsExist:
    """P0-1: task["tests"] 每个ID必须对应真实pytest函数（单一命名体系）"""

    def test_declared_tests_exist(self):
        offenders = []
        for day in range(1, 41):
            task = _load_task(day)
            declared = task.get("tests", [])
            assert declared, f"day{day:02d}.json 缺少tests字段"

            tree = ast.parse(
                (ROOT / "tests" / f"day{day:02d}_test.py").read_text(
                    encoding="utf-8"
                )
            )
            actual = _collect_test_names(tree)

            for test_id in declared:
                if test_id not in actual:
                    offenders.append(f"day{day:02d}: {test_id}")
        assert not offenders, (
            f"以下声明测试在day文件中不存在（禁止两套命名）: {offenders}"
        )

    def test_declared_tests_are_meaningful_subset(self):
        """声明数量应≥3，且不超过实际函数数（防止退化成空壳清单）"""
        for day in range(1, 41):
            task = _load_task(day)
            tree = ast.parse(
                (ROOT / "tests" / f"day{day:02d}_test.py").read_text(
                    encoding="utf-8"
                )
            )
            actual = _collect_test_names(tree)
            assert len(task.get("tests", [])) >= 3, (
                f"day{day:02d} 声明测试过少"
            )
            extra = set(task["tests"]) - actual
            assert not extra, f"day{day:02d} 幽灵声明: {extra}"


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


class TestSkillMarkerConsistency:
    """P1-4: AST解析全部类标记，要求子集关系+全覆盖"""

    def test_every_class_marker_is_subset_of_task_skills(self):
        offenders = []
        for day in range(1, 41):
            task_skills = set(_load_task(day)["skills"])
            markers = _class_skill_markers(
                ROOT / "tests" / f"day{day:02d}_test.py"
            )
            assert markers, f"day{day:02d}_test.py 无任何skill标记类"
            for cls_name, cls_skills in markers.items():
                illegal = cls_skills - task_skills
                if illegal:
                    offenders.append(
                        f"day{day:02d}.{cls_name}: 越界标签{sorted(illegal)}"
                    )
        assert not offenders, f"skill标记越界: {offenders}"

    def test_all_declared_skills_covered_by_markers(self):
        """task声明的每个skill至少被一个测试类标记覆盖"""
        uncovered = []
        for day in range(1, 41):
            task_skills = set(_load_task(day)["skills"])
            markers = _class_skill_markers(
                ROOT / "tests" / f"day{day:02d}_test.py"
            )
            union = set().union(*markers.values()) if markers else set()
            missing = task_skills - union
            if missing:
                uncovered.append(f"day{day:02d}: 未覆盖{sorted(missing)}")
        assert not uncovered, f"声明skill缺少标记覆盖: {uncovered}"
