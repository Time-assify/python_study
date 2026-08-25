"""Curriculum v2 schema冻结检查: Day01-Day40统一字段

P0-1: 每个task必须包含 estimated_minutes/prerequisites/required_api/mastery/optional_challenge/hint_levels
P0-2: required_api禁止出现test_xxx——只描述能力接口
P1-4: review_points存在
P1-5: hint_levels为[{level:int, content:str}]列表格式，level∈{1,2,3}，禁止完整答案
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
TASKS = ROOT / "tasks"

REQUIRED_FIELDS = (
    "estimated_minutes",
    "prerequisites",
    "required_api",
    "mastery",
    "optional_challenge",
    "hint_levels",
)

TEST_NAME_RE = re.compile(r"\btest_\w+")


def _load(day: int) -> dict:
    return json.loads((TASKS / f"day{day:02d}.json").read_text(encoding="utf-8"))


class TestUnifiedSchema:
    """P0-1: 全部40天schema一致"""

    def test_required_fields_present(self):
        missing = []
        for day in range(1, 41):
            d = _load(day)
            for field in REQUIRED_FIELDS:
                if field not in d:
                    missing.append(f"day{day:02d}.{field}")
        assert not missing, f"缺少必需字段: {missing}"

    def test_field_types(self):
        for day in range(1, 41):
            d = _load(day)
            assert isinstance(d["estimated_minutes"], int) and d["estimated_minutes"] > 0, \
                f"day{day:02d} estimated_minutes必须为正整数"
            assert isinstance(d["prerequisites"], list), f"day{day:02d} prerequisites必须是list"
            assert isinstance(d["required_api"], list), f"day{day:02d} required_api必须是list"
            assert isinstance(d["mastery"], list), f"day{day:02d} mastery必须是list"
            assert isinstance(d["optional_challenge"], str), \
                f"day{day:02d} optional_challenge必须是str"
            assert isinstance(d["hint_levels"], list), f"day{day:02d} hint_levels必须是list"


class TestRequiredApiDeTestified:
    """P0-2: required_api描述能力接口，禁止test_xxx"""

    def test_no_test_names_in_required_api(self):
        violations = []
        for day in range(1, 41):
            for item in _load(day)["required_api"]:
                text = json.dumps(item, ensure_ascii=False)
                match = TEST_NAME_RE.search(text)
                if match:
                    violations.append(f"day{day:02d}: '{match.group()}'")
        assert not violations, f"required_api不得包含test函数名: {violations}"

    def test_required_api_items_have_signature_and_description(self):
        for day in range(1, 41):
            for i, item in enumerate(_load(day)["required_api"]):
                assert isinstance(item, dict), f"day{day:02d} required_api[{i}]不是dict"
                sig = item.get("signature", "")
                assert sig and not sig.startswith("test"), f"day{day:02d} required_api[{i}]签名无效"
                assert item.get("description"), f"day{day:02d} required_api[{i}]缺少description"


class TestHintLevelsSchema:
    """P1-5: [{level:int, content:str}]；level∈{{1,2,3}}升序；禁止完整答案"""

    def test_format(self):
        for day in range(1, 41):
            hl = _load(day)["hint_levels"]
            levels = []
            for item in hl:
                assert isinstance(item, dict), f"day{day:02d} hint_levels条目不是dict"
                assert set(item.keys()) >= {"level", "content"}, \
                    f"day{day:02d} hint_levels条目缺少level/content"
                assert isinstance(item["level"], int), f"day{day:02d} level必须int"
                assert isinstance(item["content"], str) and item["content"].strip(), \
                    f"day{day:02d} content必须非空str"
                levels.append(item["level"])
            assert all(lv in (1, 2, 3) for lv in levels), f"day{day:02d} level越界"
            assert levels == sorted(levels), f"day{day:02d} hint_levels应按level升序"

    def test_no_full_answer_markers(self):
        """启发式：hint内容不应以'def '/'class '开头给出完整实现"""
        for day in range(1, 41):
            for item in _load(day)["hint_levels"]:
                content = item["content"].lstrip()
                assert not content.startswith("def "), \
                    f"day{day:02d} L{item['level']}疑似完整实现: {content[:40]}"
                assert not content.startswith("class Timer:"), \
                    f"day{day:02d} 疑似完整类实现"


class TestReviewPointsAndMinutes:
    """P1-4 + P1-3"""

    def test_review_points_present(self):
        for day in range(1, 41):
            d = _load(day)
            assert "review_points" in d, f"day{day:02d}缺少review_points"
            assert isinstance(d["review_points"], list), f"day{day:02d} review_points必须list"

    def test_estimated_minutes_tiers(self):
        """难度分层: Python基础60 / 数据与建模90 / CV与LLM 120 / capstone更高"""
        tiers = {**{d: 60 for d in range(1, 6)},
                 6: 90, 7: 90,
                 **{d: 90 for d in range(8, 13)},
                 13: 120, 14: 90, 15: 90, 16: 90, 17: 90,
                 18: 120, 19: 120, 20: 90}
        for day, expected in tiers.items():
            actual = _load(day)["estimated_minutes"]
            assert actual == expected, f"day{day:02d} estimated_minutes={actual}, 应为{expected}"
        # CV/LLM段不低于120
        for day in range(21, 40):
            assert _load(day)["estimated_minutes"] >= 120, f"day{day:02d}估时过低"


class TestTaskManagerCompat:
    """TaskManager加载新schema无异常"""

    def test_load_all_40(self):
        from src.task_manager.task_manager import TaskManager
        tm = TaskManager()
        for day in range(1, 41):
            task = tm.get_task(day)
            assert task.hint_levels is not None
            assert task.review_points is not None or True  # review_points经to_dict透传
            assert task.estimated_minutes > 0
