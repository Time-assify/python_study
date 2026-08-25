"""P0-1: Task schema严格类型验证（Day01-Day40遍历）

- estimated_minutes: int
- prerequisites: list[str]
- required_api: list[dict]，每项必含 name/signature/description
- mastery: list[str]
- review_points: list[str]
- hint_levels: list[dict]，每项必含 level/content
- difficulty: int 1-5
"""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
TASKS = ROOT / "tasks"


def _all_tasks():
    for day in range(1, 41):
        data = json.loads((TASKS / f"day{day:02d}.json").read_text(encoding="utf-8"))
        yield day, data


def _param_ids():
    return [f"day{d:02d}" for d in range(1, 41)]


@pytest.mark.parametrize("day", range(1, 41), ids=_param_ids())
class TestSchemaTypes:
    """每个day独立参数化，失败精确定位"""

    def test_estimated_minutes_is_positive_int(self, day):
        value = json.loads((TASKS / f"day{day:02d}.json").read_text(encoding="utf-8"))["estimated_minutes"]
        assert isinstance(value, int) and not isinstance(value, bool) and value > 0

    def test_difficulty_in_range(self, day):
        value = json.loads((TASKS / f"day{day:02d}.json").read_text(encoding="utf-8"))["difficulty"]
        assert isinstance(value, int) and not isinstance(value, bool)
        assert 1 <= value <= 5, f"difficulty必须1-5, got {value}"

    def test_prerequisites_is_list_of_str(self, day):
        data = json.loads((TASKS / f"day{day:02d}.json").read_text(encoding="utf-8"))
        assert isinstance(data["prerequisites"], list)
        for item in data["prerequisites"]:
            assert isinstance(item, str), f"prerequisites条目非str: {item!r}"

    def test_required_api_is_list_of_complete_dicts(self, day):
        data = json.loads((TASKS / f"day{day:02d}.json").read_text(encoding="utf-8"))
        api_list = data["required_api"]
        assert isinstance(api_list, list)
        for item in api_list:
            assert isinstance(item, dict), f"required_api条目必须是dict: {item!r}"
            for key in ("name", "signature", "description"):
                assert key in item, f"required_api缺少'{key}': {item!r}"
                assert isinstance(item[key], str), f"required_api.{key}必须str"
            assert item["name"].strip(), "name不能为空"
            assert item["description"].strip(), "description不能为空"

    def test_mastery_is_list_of_str(self, day):
        data = json.loads((TASKS / f"day{day:02d}.json").read_text(encoding="utf-8"))
        assert isinstance(data["mastery"], list)
        for item in data["mastery"]:
            assert isinstance(item, str), f"mastery条目非str: {item!r}"

    def test_review_points_is_list_of_str(self, day):
        data = json.loads((TASKS / f"day{day:02d}.json").read_text(encoding="utf-8"))
        rp = data.get("review_points")
        assert isinstance(rp, list)
        for item in rp:
            assert isinstance(item, str), f"review_points条目非str: {item!r}"

    def test_hint_levels_is_list_of_dicts(self, day):
        data = json.loads((TASKS / f"day{day:02d}.json").read_text(encoding="utf-8"))
        hl = data["hint_levels"]
        assert isinstance(hl, list)
        for item in hl:
            assert isinstance(item, dict), f"hint_levels条目必须是dict: {item!r}"
            assert {"level", "content"} <= set(item.keys()), \
                f"hint_levels条目缺少level/content: {item!r}"
            assert isinstance(item["level"], int), "level必须int"
            assert isinstance(item["content"], str) and item["content"].strip()


class TestDifficultyTiers:
    """P1-2难度分层建议区间"""

    @pytest.mark.parametrize("day,lo,hi", [
        *[(d, 1, 2) for d in range(1, 6)],
        *[(d, 2, 3) for d in range(6, 11)],
        *[(d, 3, 3) for d in range(11, 21)],
        *[(d, 4, 4) for d in range(21, 31)],
        *[(d, 4, 5) for d in range(31, 41)],
    ])
    def test_difficulty_in_tier(self, day, lo, hi):
        data = json.loads((TASKS / f"day{day:02d}.json").read_text(encoding="utf-8"))
        assert lo <= data["difficulty"] <= hi, \
            f"day{day} difficulty应在[{lo},{hi}]"


class TestKnowledgeGapRecord:
    """P1-1: 数据结构支持"""

    def test_create_and_to_dict(self):
        from src.models import KnowledgeGapRecord
        rec = KnowledgeGapRecord(skill="python.decorator", review_point="function", count=2)
        d = rec.to_dict()
        assert d == {"skill": "python.decorator", "review_point": "function", "count": 2}

    def test_merge_accumulates_count(self):
        from src.models import KnowledgeGapRecord
        a = KnowledgeGapRecord("tensor", "shape", 1)
        b = KnowledgeGapRecord("tensor", "shape", 3)
        assert a.merge(b).count == 4

    def test_merge_rejects_different_keys(self):
        from src.models import KnowledgeGapRecord
        a = KnowledgeGapRecord("tensor", "shape", 1)
        b = KnowledgeGapRecord("autograd", "gradient", 1)
        with pytest.raises(ValueError):
            a.merge(b)


class TestTaskDifficultyField:
    """Task dataclass支持difficulty"""

    def test_load_and_preserve(self):
        from src.task_manager.task_manager import TaskManager
        tm = TaskManager()
        task = tm.get_task(40)
        assert task.difficulty == 5
        assert task.to_dict()["difficulty"] == 5

    def test_default_difficulty(self):
        from src.task_manager.task_manager import TaskManager
        tm = TaskManager()
        assert tm.get_task(13).difficulty == 3   # Day11-20 -> 3
        assert tm.get_task(21).difficulty == 4   # Day21-30 -> 4
        assert tm.get_task(40).difficulty == 5   # capstone
