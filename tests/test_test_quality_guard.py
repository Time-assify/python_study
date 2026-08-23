"""P0-4: 验证测试质量扫描器本身有效

确保 _is_trivially_true / find_trivial_asserts 能抓住:
- assert True
- assert x or True
- assert True or x
- assert "non-empty" / assert 1 等真值常量
且不会误伤正常断言。
"""
import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from tests.test_test_quality import (  # noqa: E402
    _is_trivially_true,
    find_trivial_asserts,
)


def _asserts(code: str):
    """解析代码片段，返回所有Assert节点的test表达式"""
    tree = ast.parse(code)
    return [n.test for n in ast.walk(tree)
            if isinstance(n, ast.Assert)]


class TestTriviallyTrueDetection:
    @pytest.mark.parametrize("snippet", [
        "assert True",
        "assert x or True",
        "assert True or x",
        "assert (x or True)",
        'assert "non-empty"',
        "assert 1",
        "assert not False",
        "assert 1 or validate(x)",
        # P2: 集合字面量
        "assert [1]",
        "assert {'a': 1}",
        "assert (1,)",
        "assert {1}",
    ])
    def test_catches_tautologies(self, snippet):
        (expr,) = _asserts(snippet)
        assert _is_trivially_true(expr), (
            f"扫描器未能识别恒真断言: {snippet}"
        )

    @pytest.mark.parametrize("snippet", [
        "assert x == 5",
        "assert results",
        "assert len(items) > 0",
        "assert calls == 3",
        "assert not items",
        "assert score >= passing_score",
        "assert False",  # 恒假是合法的强制失败手段
        "assert []",     # 空集合恒假，同样是合法强制失败
    ])
    def test_does_not_flag_real_assertions(self, snippet):
        (expr,) = _asserts(snippet)
        assert not _is_trivially_true(expr), (
            f"扫描器误伤合法断言: {snippet}"
        )


class TestFindTrivialAssertsEndToEnd:
    def test_locates_all_trivial_lines(self):
        code = (
            "def test_a():\n"
            "    assert True\n"          # line 2 → 命中
            "    assert x or True\n"     # line 3 → 命中
            "    assert x == 1\n"        # 合法
            "    assert 'data'\n"        # line 5 → 命中
        )
        hits = find_trivial_asserts(ast.parse(code))
        assert sorted(hits) == [2, 3, 5], f"应命中行[2,3,5]: {hits}"

    def test_clean_tree_has_no_hits(self):
        code = (
            "def test_ok():\n"
            "    assert compute() == expected\n"
            "    assert count == 3\n"
        )
        assert find_trivial_asserts(ast.parse(code)) == []


class TestScannerSelfIntegrity:
    """扫描器必须能抓住自己仓库中的违规（若有人注入）"""

    def test_helper_rejects_or_true_pattern(self):
        """模拟绕过尝试: assert attempts >= 3 or True 必须被拦截"""
        sneaky = "attempts = {'n': 3}\nassert attempts['n'] >= 3 or True\n"
        (expr,) = _asserts(sneaky)
        assert _is_trivially_true(expr), "or True 绕过手法未被拦截"

    def test_day_files_currently_clean(self):
        """当前40个day文件必须零恒真断言（回归保护）"""
        day_files = sorted((ROOT / "tests").glob("day??_test.py"))
        offenders = []
        for f in day_files:
            for lineno in find_trivial_asserts(
                ast.parse(f.read_text(encoding="utf-8"))
            ):
                offenders.append(f"{f.name}:{lineno}")
        assert not offenders, f"day文件存在恒真断言: {offenders}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
