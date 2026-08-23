# Day90 合成判题夹具（synthetic_test.py 的运行副本，由smoke测试复制为 day90_test.py）
#
# 虚拟任务契约（与Day01-Day40正式课程完全无关）:
# - safe_divide(a, b): b==0时抛ZeroDivisionError；否则返回 a/b
# - parse_numbers(text): 提取文本中的整数/负数/小数 -> list[float]
# - Accumulator 类: add(x)返回累加后的total；total()返回当前值；reset()清零
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
        fn = _require("safe_divide")
        assert abs(fn(10, 2) - 5.0) < 1e-9

    def test_negative(self):
        """边界条件"""
        fn = _require("safe_divide")
        assert abs(fn(-9, 3) - (-3.0)) < 1e-9

    def test_zero_divisor_raises(self):
        """错误处理"""
        fn = _require("safe_divide")
        with pytest.raises(ZeroDivisionError):
            fn(1, 0)

    def test_float_result(self):
        fn = _require("safe_divide")
        assert abs(fn(1, 4) - 0.25) < 1e-9


class TestParseNumbers:
    def test_integers(self):
        fn = _require("parse_numbers")
        assert fn("a1 b22 c3") == [1.0, 22.0, 3.0]

    def test_negatives_and_decimals(self):
        """基础功能: 负号与小数"""
        fn = _require("parse_numbers")
        assert fn("x-2.5 y 3 z-7") == [-2.5, 3.0, -7.0]

    def test_no_numbers(self):
        """边界条件: 无数字返回空列表"""
        fn = _require("parse_numbers")
        assert fn("hello world") == []

    def test_mixed_text(self):
        fn = _require("parse_numbers")
        assert fn("v1.0, v2; v-3") == [1.0, 2.0, -3.0]


class TestAccumulator:
    def test_add_returns_new_total(self):
        cls = _require("Accumulator")
        acc = cls()
        assert acc.add(5) == 5
        assert acc.add(3) == 8

    def test_total_and_initial(self):
        """边界条件: 初始total为0"""
        cls = _require("Accumulator")
        acc = cls()
        assert acc.total() == 0
        acc.add(2)
        acc.add(2)
        assert acc.total() == 4

    def test_reset_clears(self):
        """错误处理路径之外的完整生命周期"""
        cls = _require("Accumulator")
        acc = cls()
        acc.add(10)
        acc.reset()
        assert acc.total() == 0
        assert acc.add(1) == 1

    def test_negative_values(self):
        cls = _require("Accumulator")
        acc = cls()
        acc.add(-5)
        acc.add(2)
        assert acc.total() == -3
