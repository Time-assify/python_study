# Day90 合成Pipeline夹具（与Day01-Day40正式课程完全无关）
#
# 虚拟任务契约:
# - safe_divide(a, b): b==0抛ZeroDivisionError；否则返回 a/b
# - normalize_name(s): 去首尾空格、压缩连续空格为单个、每个单词首字母大写
#     例: "  john   DOE " -> "John Doe"
# - Accumulator: add(x)返回累加后的total；total()取值；reset()清零
import pytest

try:
    import answer
except ModuleNotFoundError as e:
    if getattr(e, "name", "") == "answer":
        answer = None
    else:
        raise
except Exception:
    raise


def test_answer_module_imports():
    if answer is None:
        pytest.skip("no answer.py under review")


def _require(name):
    if answer is None:
        pytest.skip("no answer.py under review")
    obj = getattr(answer, name, None)
    if obj is None:
        pytest.fail(f"必须实现 {name}")
    return obj


class TestSafeDivide:
    def test_basic(self):
        assert abs(_require("safe_divide")(10, 4) - 2.5) < 1e-9

    def test_zero_raises(self):
        """错误处理"""
        with pytest.raises(ZeroDivisionError):
            _require("safe_divide")(1, 0)

    def test_negative(self):
        """边界条件"""
        assert abs(_require("safe_divide")(-7, 2) - (-3.5)) < 1e-9


class TestNormalizeName:
    def test_basic(self):
        fn = _require("normalize_name")
        assert fn("john doe") == "John Doe"

    def test_collapses_whitespace(self):
        """基础功能: 多空格折叠"""
        fn = _require("normalize_name")
        assert fn("  john   DOE  ") == "John Doe"

    def test_empty_string(self):
        """边界条件"""
        fn = _require("normalize_name")
        assert fn("") == ""

    def test_single_word(self):
        fn = _require("normalize_name")
        assert fn("ALICE") == "Alice"


class TestAccumulator:
    def test_add_chains(self):
        cls = _require("Accumulator")
        acc = cls()
        assert acc.add(2) == 2 and acc.add(3) == 5

    def test_total(self):
        cls = _require("Accumulator")
        acc = cls()
        acc.add(1.5)
        acc.add(2.5)
        assert acc.total() == 4.0

    def test_reset(self):
        """完整生命周期"""
        cls = _require("Accumulator")
        acc = cls()
        acc.add(9)
        acc.reset()
        assert acc.total() == 0

    def test_negative_accumulation(self):
        cls = _require("Accumulator")
        acc = cls()
        acc.add(-4)
        acc.add(1)
        assert acc.total() == -3
