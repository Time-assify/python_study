# -*- coding: utf-8 -*-
"""P0-1: knowledge point registry 一致性校验（v1.0冻结）

- config/knowledge_points.yaml是唯一定义源（id/name/category/level）
- Task.skills / 测试skill marker / SKILL_LABELS 均只能引用registry中存在的id
"""
import ast
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
REGISTRY_PATH = ROOT / "config" / "knowledge_points.yaml"
TASKS = ROOT / "tasks"
TESTS = ROOT / "tests"


def _registry() -> dict:
    data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8")) or {}
    return {e["id"]: e for e in data.get("knowledge_points", [])}


def _task_skill_ids():
    ids = set()
    for p in sorted(TASKS.glob("day*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        ids.update(d.get("skills", []))
    return ids


def _test_marker_ids():
    """AST收集全部day测试的@pytest.mark.skill(...)参数"""
    import re
    ids = set()
    pattern = re.compile(r"skill\(([^)]*)\)")
    for p in sorted(TESTS.glob("day*_test.py")):
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                continue
            for dec in node.decorator_list:
                src = ast.unparse(dec)
                m = pattern.search(src)
                if m:
                    for lit in re.findall(r'"([^"]+)"|\'([^\']+)\'', m.group(1)):
                        ids.add(lit[0] or lit[1])
    return ids


class TestRegistryIntegrity:
    def test_registry_loads(self):
        reg = _registry()
        assert len(reg) >= 80, f"registry条目过少: {len(reg)}"

    def test_entries_have_required_fields(self):
        for sid, meta in _registry().items():
            assert {"name", "category", "level"} <= set(meta), \
                f"{sid}缺少name/category/level"
            assert isinstance(meta["name"], str) and meta["name"].strip()
            assert meta["level"] in (1, 2, 3)

    def test_ids_unique(self):
        raw = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
        ids = [e["id"] for e in raw["knowledge_points"]]
        assert len(ids) == len(set(ids)), "registry存在重复id"


class TestReferencesResolve:
    def test_task_skills_in_registry(self):
        missing = _task_skill_ids() - set(_registry())
        assert not missing, f"Task引用了未注册的knowledge point: {missing}"

    def test_test_markers_in_registry(self):
        missing = _test_marker_ids() - set(_registry())
        assert not missing, f"测试marker引用了未注册的knowledge point: {missing}"

    def test_no_orphan_registry_entries(self):
        """registry中的id必须被Task或测试实际使用（防死条目）"""
        used = _task_skill_ids() | _test_marker_ids()
        orphans = set(_registry()) - used
        assert not orphans, f"registry存在未被引用的条目: {orphans}"


class TestSkillMapperUsesRegistry:
    def test_labels_match_registry_names(self):
        from src.analyzer.skill_mapper import SKILL_LABELS
        reg = _registry()
        for sid, name in SKILL_LABELS.items():
            assert sid in reg, f"SKILL_LABELS含未注册id: {sid}"
            assert name == reg[sid]["name"], f"{sid}名称与registry不一致"

    def test_get_knowledge_point(self):
        from src.analyzer.skill_mapper import get_knowledge_point
        kp = get_knowledge_point("python.decorator")
        assert kp == {"name": "装饰器", "category": "python", "level": 1}
        assert get_knowledge_point("nonexistent.skill") is None

    def test_build_records_uses_registry_names(self):
        from src.analyzer.skill_mapper import SkillMapper
        records = SkillMapper().build_records(
            2, ["tests/day02_test.py::TestDecorators::test_memoize_caches_results"]
        )
        reg = _registry()
        for r in records:
            assert r.knowledge_point["name"] == reg[r.skill]["name"]
