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
        *[(d, 3, 3) for d in range(31, 34)],   # P1-1: LLM基础段降为3
        *[(d, 4, 4) for d in range(34, 37)],   # RAG段
        *[(d, 4, 5) for d in range(37, 40)],   # Agent段
        (40, 5, 5),
    ])
    def test_difficulty_in_tier(self, day, lo, hi):
        data = json.loads((TASKS / f"day{day:02d}.json").read_text(encoding="utf-8"))
        assert lo <= data["difficulty"] <= hi, \
            f"day{day} difficulty应在[{lo},{hi}]"


class TestKnowledgeGapRecord:
    """P1-1/P0-1: 数据结构支持"""

    def test_create_and_to_dict(self):
        from src.models import KnowledgeGapRecord
        rec = KnowledgeGapRecord(
            skill="python.decorator",
            knowledge_point={"id": "python.decorator", "name": "装饰器"},
            review_point="function",
            count=2,
        )
        d = rec.to_dict()
        assert d["skill"] == "python.decorator"
        assert d["knowledge_point"] == {"id": "python.decorator", "name": "装饰器"}
        assert d["review_point"] == "function"
        assert d["count"] == 2

    def test_knowledge_point_autofilled_from_skill(self):
        from src.models import KnowledgeGapRecord
        rec = KnowledgeGapRecord(skill="tensor")
        assert rec.knowledge_point == {"id": "tensor", "name": "tensor"}

    def test_merge_accumulates_count(self):
        from src.models import KnowledgeGapRecord
        a = KnowledgeGapRecord("tensor", None, "shape", 1)
        b = KnowledgeGapRecord("tensor", {"id": "tensor", "name": "t"}, "shape", 3)
        merged = a.merge(b)
        assert merged.count == 4
        assert merged.review_point == "shape"

    def test_merge_rejects_different_keys(self):
        from src.models import KnowledgeGapRecord
        a = KnowledgeGapRecord("tensor", None, "shape", 1)
        b = KnowledgeGapRecord("autograd", None, "gradient", 1)
        with pytest.raises(ValueError):
            a.merge(b)


class TestSkillMapper:
    """P0-1: 测试失败 -> skill映射"""

    def _mapper(self, tmp_path):
        from src.analyzer.skill_mapper import SkillMapper
        return SkillMapper(tests_dir=Path(__file__).parent)

    def test_build_index_day02(self):
        from src.analyzer.skill_mapper import SkillMapper
        mapper = SkillMapper()
        index = mapper.build_index(2)
        assert index.get("test_repeat_executes_n_times") == \
            ["python.decorator", "python.generator", "python.context_manager"]
        # 模块级函数无skill标记，不进索引
        assert "test_answer_module_imports" not in index

    def test_map_failures_nodeid_and_counts(self):
        from src.analyzer.skill_mapper import SkillMapper
        mapper = SkillMapper()
        failed = [
            "tests/day02_test.py::TestDecorators::test_repeat_executes_n_times",
            "tests/day02_test.py::TestGenerators::test_fibonacci_yields_n_terms",
            "tests/day02_test.py::TestGenerators::test_fibonacci_zero_terms",
        ]
        counts = mapper.map_failures(2, failed)
        # day02所有类携带同一组skill标记，每个失败测试贡献全部3个skill
        assert counts["python.generator"] == 3
        assert counts["python.decorator"] == 3
        assert counts["python.context_manager"] == 3

    def test_build_records_structure(self):
        from src.analyzer.skill_mapper import SkillMapper
        mapper = SkillMapper()
        records = mapper.build_records(2, ["tests/day02_test.py::TestDecorators::test_memoize_caches_results"])
        assert len(records) == 3
        dec = next(r for r in records if r.skill == "python.decorator")
        assert dec.count == 1
        assert dec.knowledge_point == {"id": "python.decorator", "name": "装饰器"}

    def test_unknown_test_ignored(self):
        from src.analyzer.skill_mapper import SkillMapper
        mapper = SkillMapper()
        assert mapper.build_records(99, ["whatever_test"]) == []


class TestKnowledgeGapPersistence:
    """P0-1: 记录入库与聚合"""

    def test_save_and_aggregate(self, tmp_path):
        import sys
        sys.path.insert(0, str(ROOT))
        from src.database import Database
        db = Database(db_path=str(tmp_path / "t.db"))
        from src.models import KnowledgeGapRecord
        records = [
            KnowledgeGapRecord("python.decorator",
                               {"id": "python.decorator", "name": "装饰器"}, "", 2),
            KnowledgeGapRecord("python.generator",
                               {"id": "python.generator", "name": "生成器"}, "", 1),
            KnowledgeGapRecord("python.decorator",
                               {"id": "python.decorator", "name": "装饰器"}, "", 3),
        ]
        saved = db.save_knowledge_gap_records(2, records)
        assert saved == 3
        agg = db.get_knowledge_gap_records()
        top = agg[0]
        assert top["skill"] == "python.decorator"
        assert top["count"] == 5
        assert top["knowledge_point"]["name"] == "装饰器"


class TestDifficultyRecommendation:
    """P0-2: 连击难度规则"""

    def test_two_failures_reduce_difficulty(self):
        from src.agents.learning_advisor import LearningAdvisor
        recent = [{"passed": False, "difficulty": 3},
                  {"passed": False, "difficulty": 3},
                  {"passed": True, "difficulty": 3}]
        rec = LearningAdvisor.recommend_difficulty(recent, current_difficulty=3)
        assert rec["mode"] == "reduce"
        assert rec["max_difficulty"] <= 3

    def test_three_passes_allow_advance(self):
        from src.agents.learning_advisor import LearningAdvisor
        recent = [{"passed": True, "difficulty": 3}] * 3
        rec = LearningAdvisor.recommend_difficulty(recent, current_difficulty=3)
        assert rec["mode"] == "advance"
        assert rec["max_difficulty"] == 4

    def test_mixed_history_maintains(self):
        from src.agents.learning_advisor import LearningAdvisor
        recent = [{"passed": True, "difficulty": 3},
                  {"passed": False, "difficulty": 3},
                  {"passed": False, "difficulty": 4}]
        rec = LearningAdvisor.recommend_difficulty(recent, current_difficulty=3)
        assert rec["mode"] == "maintain"
        assert rec["max_difficulty"] == 3

    def test_advice_includes_recommendation(self):
        from src.agents.learning_advisor import LearningAdvisor
        from src.models import StudentProfile
        advisor = LearningAdvisor()
        profile = StudentProfile(error_statistics={"LogicError": 1})
        advice = advisor.generate_advice(
            profile,
            recent_results=[{"passed": True, "difficulty": 3}] * 4,
            current_difficulty=3,
        )
        assert advice.difficulty_recommendation is not None
        assert advice.difficulty_recommendation["max_difficulty"] >= 4


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
