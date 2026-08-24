# Day 02 Tests: 高级Python
#
# 核心接口（Timer上下文管理器已移至可选挑战:
#   tests/challenges/day02_challenge_test.py）:
# - repeat(n)                      装饰器工厂：被装饰函数执行n次，返回最后一次结果；n<=0 抛 ValueError
# - memoize(func)                  装饰器：缓存相同参数的调用结果
# - fibonacci(n)                   生成器函数：yield前n个斐波那契数
# - chunked(iterable, size)        生成器函数：按size分块yield列表；size<1 抛 ValueError
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
    """answer exists -> import errors are FAIL; only skip when repo has no submission"""
    if answer is None:
        pytest.skip("no answer.py under review (TestEngine injects it during real grading)")


def _require(name):
    if answer is None:
        pytest.skip("no answer.py under review")
    fn = getattr(answer, name, None)
    if fn is None:
        pytest.fail(f"必须实现 {name}()")
    return fn


@pytest.mark.skill("python.decorator", "python.generator", "python.context_manager")
class TestDecorators:
    """基础功能: 装饰器"""

    def test_repeat_executes_n_times(self):
        repeat = _require("repeat")

        calls = []

        @repeat(3)
        def work():
            calls.append(1)
            return "done"

        result = work()
        assert len(calls) == 3, f"应执行3次，实际{len(calls)}次"
        assert result == "done", "repeat应返回最后一次执行结果"

    def test_repeat_invalid_n_raises(self):
        """错误处理: n<=0 应抛 ValueError"""
        repeat = _require("repeat")

        @repeat(-1)
        def work():
            return 1

        with pytest.raises(ValueError):
            work()

    def test_memoize_caches_results(self):
        memoize = _require("memoize")
        count = {"n": 0}

        @memoize
        def slow_add(a, b):
            count["n"] += 1
            return a + b

        assert slow_add(2, 3) == 5
        assert slow_add(2, 3) == 5
        assert slow_add(2, 3) == 5
        assert count["n"] == 1, f"相同参数应命中缓存，实际计算了{count['n']}次"
        assert slow_add(4, 4) == 8
        assert count["n"] == 2


@pytest.mark.skill("python.decorator", "python.generator", "python.context_manager")
class TestGenerators:
    """基础功能+边界条件: 生成器"""

    def test_fibonacci_yields_n_terms(self):
        fib = _require("fibonacci")
        import types
        gen = fib(6)
        assert isinstance(gen, types.GeneratorType), "fibonacci必须是生成器函数"
        values = list(gen)
        assert values == [0, 1, 1, 2, 3, 5], f"错误结果: {values}"

    def test_fibonacci_zero_terms(self):
        """边界条件: n=0 应为空"""
        fib = _require("fibonacci")
        assert list(fib(0)) == []

    def test_chunked_splits_correctly(self):
        chunked = _require("chunked")
        chunks = list(chunked(range(7), 3))
        assert chunks[0] == [0, 1, 2]
        assert chunks[2] == [6], "最后一块可以不足size"

    def test_chunked_invalid_size_raises(self):
        """错误处理: size<1"""
        chunked = _require("chunked")
        with pytest.raises(ValueError):
            list(chunked([1, 2, 3], 0))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
