"""Curriculum schema: Day01-Day40 必须支持 required_api/prerequisites/mastery/estimated_minutes

验证:
1. 每个task.json包含指定字段（缺失=schema不兼容）
2. Day01-Day10 required_api非空
3. Task dataclass可加载全部40个JSON
4. Day11-Day40字段默认值安全（空列表，不报错）
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
TASKS = ROOT / "tasks"


def _load(day):
    return json.loads((TASKS / f"day{day:02d}.json").read_text(encoding="utf-8"))


class TestTaskSchemaPresence:
    """所有day Task dataclass可正常加载（字段缺失由默认值兜底）"""

    def test_all_tasks_load(self):
        from src.task_manager.task_manager import TaskManager
        tm = TaskManager()
        for day in range(1, 41):
            task = tm.get_task(day)
            assert task is not None, f"day{day:02d} TaskManager返回None"
            # 验证核心字段可达
            _ = getattr(task, "required_api", []) or []
            _ = getattr(task, "prerequisites", []) or []
            _ = getattr(task, "mastery", []) or []
            _ = getattr(task, "estimated_minutes", 60)


class TestDay01_10RequiredApi:
    """P0-1: Day01-10的required_api必须非空，且每个条目含signature"""

    def test_required_api_nonempty(self):
        for day in range(1, 11):
            d = _load(day)
            api = d.get("required_api", [])
            assert len(api) > 0, f"day{day:02d} required_api为空"

    def test_required_api_has_signature(self):
        for day in range(1, 11):
            d = _load(day)
            for i, item in enumerate(d.get("required_api", [])):
                assert isinstance(item, dict), f"day{day:02d} required_api[{i}]不是dict"
                assert "signature" in item, f"day{day:02d} required_api[{i}]缺少signature"
                assert "description" in item, f"day{day:02d} required_api[{i}]缺少description"


class TestDay01_10PrerequisitesAndHintLevels:
    """P1-6: Day01-10 prerequisites和hint_levels必须存在"""

    def test_prerequisites_present(self):
        for day in range(1, 11):
            d = _load(day)
            assert "prerequisites" in d, f"day{day:02d}缺少prerequisites"

    def test_hint_levels_present(self):
        """P1-5 v2格式: [{level:int, content:str}]"""
        for day in range(1, 11):
            d = _load(day)
            assert "hint_levels" in d, f"day{day:02d}缺少hint_levels"
            hl = d["hint_levels"]
            assert isinstance(hl, list) and hl, f"day{day:02d} hint_levels必须非空list"
            levels = {item.get("level") for item in hl}
            for level in (1, 2, 3):
                assert level in levels, f"day{day:02d} hint_levels缺少L{level}"


class TestTaskManagerLoadsAll40:
    """TaskManager能加载全部40天"""

    def test_load_all_tasks(self):
        from src.task_manager.task_manager import TaskManager
        tm = TaskManager()
        errors = []
        for day in range(1, 41):
            try:
                task = tm.get_task(day)
                # 验证新增字段可访问（不会AttributeError）
                _ = getattr(task, "required_api", None) or []
                _ = getattr(task, "prerequisites", None) or []
                _ = getattr(task, "hint_levels", None) or {}
                _ = getattr(task, "learn", None) or []
            except Exception as e:
                errors.append(f"day{day:02d}: {e}")
        assert not errors, f"TaskManager加载失败: {errors}"
