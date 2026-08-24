# Day 04 Tests: 多线程/并发（核心聚焦ThreadPoolExecutor）
#
# 核心接口（multiprocessing已移至可选挑战:
#   tests/challenges/day04_challenge_test.py）:
# - run_in_threads(func, n) -> list     用n个线程执行func(i)，返回结果列表
# - concurrent_map(func, items) -> list 用ThreadPoolExecutor映射，保持输入顺序
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

import threading


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


@pytest.mark.skill("python.threading", "python.multiprocessing")
class TestThreads:
    def test_run_in_threads_executes_all(self):
        run_in_threads = _require("run_in_threads")
        results = run_in_threads(lambda i: i * 10, 5)
        assert len(results) == 5, f"应有5个结果，得到{len(results)}"
        assert sorted(results) == [0, 10, 20, 30, 40]

    def test_run_in_threads_uses_threads(self):
        """任务要求检查: 确实在线程中执行"""
        run_in_threads = _require("run_in_threads")
        seen_threads = []
        run_in_threads(lambda i: seen_threads.append(threading.current_thread()), 3)
        main = threading.current_thread()
        assert any(t is not main for t in seen_threads), "工作必须发生在子线程中"

    def test_zero_threads(self):
        """边界条件: n=0 返回空列表"""
        run_in_threads = _require("run_in_threads")
        assert list(run_in_threads(lambda i: i, 0)) == []


@pytest.mark.skill("python.threading", "python.multiprocessing")
class TestConcurrentMap:
    def test_order_preserved(self):
        concurrent_map = _require("concurrent_map")
        items = list(range(20))
        result = concurrent_map(lambda x: x + 1, items)
        assert result == [x + 1 for x in items], "ThreadPoolExecutor映射必须保持顺序"

    def test_empty_items(self):
        """边界条件: 空输入"""
        concurrent_map = _require("concurrent_map")
        assert concurrent_map(str, []) == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
