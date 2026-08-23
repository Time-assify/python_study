# Day 04 Tests: 多线程/多进程
#
# answer.py 必须实现（接口约定）:
# - run_in_threads(func, n) -> list     用n个线程执行func(i)，按完成顺序或提交顺序返回结果
# - concurrent_map(func, items) -> list 用ThreadPoolExecutor映射，保持输入顺序
# - make_process(target) -> multiprocessing.Process  创建进程对象（不要求启动）
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
import multiprocessing


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


@pytest.mark.skill("python.threading", "python.multiprocessing")
class TestProcess:
    def test_make_process_returns_process(self):
        if answer is None:
            pytest.skip("no answer.py under review")
        make_process = getattr(answer, "make_process", None)
        if make_process is None:
            pytest.fail("必须实现 make_process()")
        p = make_process(lambda: None)
        # 兼容直接返回Process对象或返回可调用工厂
        if isinstance(p, multiprocessing.process.BaseProcess):
            proc = p
        elif callable(p):
            proc = p()
        else:
            pytest.fail("make_process应返回Process对象")
        assert isinstance(proc, multiprocessing.process.BaseProcess)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
