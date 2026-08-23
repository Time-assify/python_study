# Day 39 Tests: Agent系统集成
#
# answer.py 必须实现（接口约定）:
# - Pipeline(steps)  .run(x) -> 按顺序链式执行各step的输出作为下一步输入
# - retry_step(step, retries=2) -> wrapped   失败自动重试，超过次数抛原异常
# - EventBus()  .subscribe(topic, fn) / .publish(topic, data)
# - health_check(services) -> dict  services为{name: callable}；
#   返回 {"all_ok": bool, "failures": [name,...]}
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
    obj = getattr(answer, name, None)
    if obj is None:
        pytest.fail(f"必须实现 {name}")
    return obj


@pytest.mark.skill("system.pipeline", "system.event_bus")
class TestPipeline:
    def test_chains_outputs(self):
        pipe_cls = _require("Pipeline")
        p = pipe_cls([lambda x: x + 1, lambda x: x * 10, lambda s: f"v={s}"])
        assert p.run(4) == "v=50", "步骤必须链式传递"

    def test_single_and_empty(self):
        """边界条件"""
        pipe_cls = _require("Pipeline")
        assert pipe_cls([lambda x: x + 1]).run(1) == 2
        assert pipe_cls([]).run("same") == "same"

    def test_error_propagates(self):
        """错误处理: step异常向上传播"""
        pipe_cls = _require("Pipeline")

        def boom(_):
            raise RuntimeError("bad")

        with pytest.raises(RuntimeError):
            pipe_cls([boom]).run(0)


@pytest.mark.skill("system.pipeline", "system.event_bus")
class TestRetry:
    def test_retry_then_success(self):
        retry_step = _require("retry_step")
        calls = {"n": 0}

        @retry_step
        def flaky(x):
            calls["n"] += 1
            if calls["n"] < 3:
                raise ValueError("not yet")
            return x * 2

        # retry_step可作为装饰器或工厂；两种用法都兼容
        result = flaky(5)
        assert result == 10 and calls["n"] == 3

    def test_retries_exhausted_raises(self):
        if answer is None:
            pytest.skip("no answer.py under review")
        retry_fn = getattr(answer, "retry_step", None)
        if retry_fn is None:
            pytest.fail("必须实现 retry_step()")
        attempts = {"n": 0}
        wrapped = retry_fn(lambda x: attempts.__setitem__("n", attempts["n"] + 1) or 1 / 0, retries=2)
        with pytest.raises(ZeroDivisionError):
            wrapped(0)
        # retries=2 → 首次调用 + 2次重试 = 3次
        assert attempts["n"] == 3, f"重试次数错误：期望3次，实际{attempts['n']}次"


@pytest.mark.skill("system.pipeline", "system.event_bus")
class TestEventBus:
    def test_pubsub_delivers(self):
        bus_cls = _require("EventBus")
        bus = bus_cls()
        got = []
        bus.subscribe("train", lambda d: got.append(d))
        bus.publish("train", {"epoch": 1})
        assert got == [{"epoch": 1}]

    def test_unsubscribed_topic_ignored(self):
        bus_cls = _require("EventBus")
        bus_cls().publish("nobody-listening", 123)  # 不应抛错

    def test_multiple_subscribers(self):
        bus_cls = _require("EventBus")
        bus = bus_cls()
        hits = []
        bus.subscribe("t", lambda d: hits.append("a"))
        bus.subscribe("t", lambda d: hits.append("b"))
        bus.publish("t", None)
        assert sorted(hits) == ["a", "b"]


@pytest.mark.skill("system.pipeline", "system.event_bus")
class TestHealthCheck:
    def test_all_ok(self):
        hc = _require("health_check")
        report = hc({"db": lambda: True, "cache": lambda: True})
        assert report.get("all_ok") is True and report.get("failures") == []

    def test_failure_reported(self):
        """错误处理: 服务挂掉要进failures且all_ok=False"""

        def dead():
            raise ConnectionError("down")

        hc = _require("health_check")
        report = hc({"api": dead, "ok_svc": lambda: True})
        assert report.get("all_ok") is False
        assert "api" in report.get("failures", [])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
