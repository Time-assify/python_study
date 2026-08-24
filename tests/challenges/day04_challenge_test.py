# Day04 可选挑战: multiprocessing（不计入当天核心分数）
#
# answer.py 需额外实现:
# - make_process(target) -> multiprocessing.Process  创建进程对象（不要求启动）
import multiprocessing

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


@pytest.mark.challenge
class TestProcessChallenge:
    def test_make_process_returns_process(self):
        if answer is None:
            pytest.skip("no answer.py under review")
        make_process = getattr(answer, "make_process", None)
        if make_process is None:
            pytest.fail("必须实现 make_process()")
        p = make_process(lambda: None)
        if isinstance(p, multiprocessing.process.BaseProcess):
            proc = p
        elif callable(p):
            proc = p()
        else:
            pytest.fail("make_process应返回Process对象")
        assert isinstance(proc, multiprocessing.process.BaseProcess)
