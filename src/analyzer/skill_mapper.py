# -*- coding: utf-8 -*-
"""SkillMapper: 测试失败 -> skill -> KnowledgeGapRecord (P0-1)

通过AST解析 tests/dayXX_test.py 中类级 @pytest.mark.skill(...) 标记，
建立 {测试函数名: [skills]} 索引；失败时自动映射并生成
KnowledgeGapRecord(skill, knowledge_point={id,name}, count)。

不修改Evaluator架构——只读取其产出的失败测试名列表。
"""
import ast
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from ..models import KnowledgeGapRecord


@lru_cache(maxsize=1)
def _load_registry() -> Dict[str, dict]:
    """加载知识点注册表 config/knowledge_points.yaml（P0-1: 唯一定义源）

    Returns:
        {id: {name, category, level}}
    """
    import yaml
    path = Path(__file__).parent.parent.parent / "config" / "knowledge_points.yaml"
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    registry = {}
    for entry in data.get("knowledge_points", []):
        registry[entry["id"]] = {
            "name": entry["name"],
            "category": entry["category"],
            "level": int(entry["level"]),
        }
    return registry


def get_knowledge_point(skill_id: str) -> Optional[dict]:
    """查询知识点定义；未注册的id返回None"""
    return _load_registry().get(skill_id)


# 兼容旧用法：id -> 中文名（来自注册表派生）
SKILL_LABELS: Dict[str, str] = {}

def _refresh_labels():
    SKILL_LABELS.clear()
    for sid, meta in _load_registry().items():
        SKILL_LABELS[sid] = meta["name"]

_refresh_labels()

# skill id -> 中文知识点名（用于knowledge_point.name）

_NODEID_TAIL = re.compile(r"([\w]+)::(?:[\w]+::)*([A-Za-z_][A-Za-z0-9_]*)\s*$")


def _extract_test_name(raw: str) -> str:
    """从nodeid或裸函数名中提取测试函数名

    'tests/day02_test.py::TestDecorators::test_repeat_executes_n_times'
      -> 'test_repeat_executes_n_times'
    """
    m = _NODEID_TAIL.search(raw)
    return m.group(2) if m else raw.strip()


class SkillMapper:
    """day级 {测试函数名: skills} 索引与失败映射"""

    def __init__(self, tests_dir: Optional[Path] = None):
        self.tests_dir = Path(tests_dir) if tests_dir else Path(__file__).parent.parent.parent / "tests"
        self._index_cache: Dict[int, Dict[str, List[str]]] = {}

    def build_index(self, day: int) -> Dict[str, List[str]]:
        """AST解析 day{day}_test.py，返回 {测试函数名: [skill,...]}（带缓存）"""
        if day in self._index_cache:
            return self._index_cache[day]
        path = self.tests_dir / f"day{day:02d}_test.py"
        index: Dict[str, List[str]] = {}
        if path.exists():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    class_skills = self._skills_from_decorator(node)
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                                and item.name.startswith("test_"):
                            # 类内方法继承类标记；方法自带标记则合并
                            own = self._skills_from_decorator(item)
                            merged = list(dict.fromkeys(class_skills + own))
                            if merged:
                                index[item.name] = merged
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                        and node.name.startswith("test_"):
                    own = self._skills_from_decorator(node)
                    if own:
                        index[node.name] = own
        self._index_cache[day] = index
        return index

    @staticmethod
    def _skills_from_decorator(node) -> List[str]:
        skills: List[str] = []
        for dec in node.decorator_list:
            call = dec.func if isinstance(dec, ast.Call) else dec
            if isinstance(call, ast.Attribute) and call.attr == "skill":
                args = dec.args if isinstance(dec, ast.Call) else []
            elif isinstance(call, ast.Name) and call.id == "skill":
                args = dec.args if isinstance(dec, ast.Call) else []
            else:
                continue
            for arg in args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    skills.append(arg.value)
        return skills

    def map_failures(self, day: int, failed_test_names: List[str]) -> Dict[str, int]:
        """失败测试名 -> {skill: 失败次数}"""
        index = self.build_index(day)
        counter: Counter = Counter()
        for raw in failed_test_names:
            name = _extract_test_name(raw)
            for skill in index.get(name, []):
                counter[skill] += 1
        return dict(counter)

    def build_records(self, day: int, failed_test_names: List[str]) -> List[KnowledgeGapRecord]:
        """失败测试 -> KnowledgeGapRecord列表（按skill聚合计数）"""
        records = []
        for skill, count in sorted(self.map_failures(day, failed_test_names).items()):
            label = SKILL_LABELS.get(skill, skill)
            records.append(KnowledgeGapRecord(
                skill=skill,
                knowledge_point={"id": skill, "name": label},
                count=count,
            ))
        return records
