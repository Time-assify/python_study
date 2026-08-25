# -*- coding: utf-8 -*-
"""P1-1: hint质量分级检查（Day01-Day40）

规则:
- L1: 不能包含代码块——禁止```围栏、def/class/import语句、赋值语句'='
- L2: 不能包含完整函数实现——禁止```围栏、以def/class开头的内容
- L3: 允许伪代码；仍禁止完整答案（不以def/class开头、无```围栏）
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
TASKS = ROOT / "tasks"

ASSIGN_RE = re.compile(r"(?<![=!<>])=(?!=)")
STMT_START_RE = re.compile(r"^\s*(def |class |import |from )")


def _hint_levels(day: int, level: int):
    data = json.loads((TASKS / f"day{day:02d}.json").read_text(encoding="utf-8"))
    return [h["content"] for h in data.get("hint_levels", []) if h.get("level") == level]


@pytest.mark.parametrize("day", range(1, 41), ids=[f"day{d:02d}" for d in range(1, 41)])
class TestHintLevelQuality:
    def test_level1_no_code(self, day):
        for content in _hint_levels(day, 1):
            assert "```" not in content, f"day{day} L1含代码围栏: {content[:40]}"
            assert not STMT_START_RE.search(content), f"day{day} L1含代码语句: {content[:40]}"
            assert not ASSIGN_RE.search(content), f"day{day} L1含赋值'=': {content[:40]}"

    def test_level2_no_full_implementation(self, day):
        for content in _hint_levels(day, 2):
            assert "```" not in content, f"day{day} L2含代码围栏"
            assert not content.lstrip().startswith("def "), \
                f"day{day} L2疑似完整函数实现: {content[:40]}"
            assert not content.lstrip().startswith("class "), \
                f"day{day} L2疑似完整类实现: {content[:40]}"

    def test_level3_pseudocode_not_full_answer(self, day):
        for content in _hint_levels(day, 3):
            assert "```" not in content, f"day{day} L3含代码围栏"
            assert not content.lstrip().startswith("def "), \
                f"day{day} L3疑似完整答案: {content[:40]}"
            assert not content.lstrip().startswith("class "), \
                f"day{day} L3疑似完整类答案: {content[:40]}"


class TestHintLevelProgression:
    """L1应比L2更抽象：同一任务中L1不得比L3/L2出现更多具体代码记号"""

    @pytest.mark.parametrize("day", [d for d in range(1, 41)
                                     if _hint_levels(d, 1) and _hint_levels(d, 3)],
                             ids=lambda d: f"day{d:02d}")
    def test_l1_exists_whenever_l3_exists(self, day):
        assert _hint_levels(day, 1), f"day{day}有L3却无L1，提示阶梯断裂"
