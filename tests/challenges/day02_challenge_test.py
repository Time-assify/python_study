# Day02 可选挑战: Timer上下文管理器（不计入当天核心分数）
#
# answer.py 需额外实现:
# - Timer 类: with结束后可通过 .elapsed 获取耗时(秒)
import time

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
class TestTimerChallenge:
    def test_timer_measures_elapsed(self):
        if answer is None:
            pytest.skip("no answer.py under review")
        timer_cls = getattr(answer, "Timer", None)
        if timer_cls is None:
            pytest.fail("必须实现 Timer 类（上下文管理器）")
        with timer_cls() as t:
            time.sleep(0.05)
        elapsed = getattr(t, "elapsed", None)
        assert elapsed is not None, "退出with后Timer应有elapsed属性"
        assert elapsed >= 0.04, f"计时偏差过大: {elapsed}"
