# Day 30 Tests: AI应用整合
#
# answer.py 必须实现（接口约定）:
# - AppConfig                        dataclass，字段 name:str, model:str, temperature:float
#   含 from_dict(d) / to_dict()；缺字段抛 KeyError/TypeError
# - save_config(config, path) / load_config(path)   yaml持久化roundtrip
# - PipelineApp                      register_handler(fn)按注册顺序执行 run(x)->list结果
# - Monitor                          计数器 record(event) / count(event)
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

try:
    import yaml  # noqa
except ImportError:
    yaml = None


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


class TestAppConfig:
    def test_roundtrip(self):
        cls = _require("AppConfig")
        cfg = cls(name="demo", model="gpt-x", temperature=0.7)
        d = cfg.to_dict()
        assert d["name"] == "demo" and abs(d["temperature"] - 0.7) < 1e-9
        cfg2 = cls.from_dict(d)
        assert cfg2.name == cfg.name and cfg2.model == cfg.model

    def test_missing_key_raises(self):
        """错误处理: 缺少必需字段"""
        cls = _require("AppConfig")
        with pytest.raises((KeyError, TypeError)):
            cls.from_dict({"name": "only-name"})


@pytest.mark.skipif(yaml is None, reason="pyyaml未安装（环境问题）")
class TestConfigPersistence:
    def test_save_load_yaml(self, tmp_path):
        if answer is None:
            pytest.skip("no answer.py under review")
        save_config = getattr(answer, "save_config", None)
        load_config = getattr(answer, "load_config", None)
        if save_config is None or load_config is None:
            pytest.fail("必须实现 save_config()/load_config()")
        cls = _require("AppConfig")
        path = str(tmp_path / "cfg.yaml")
        save_config(cls(name="svc", model="m1", temperature=0.3), path)
        cfg = load_config(path)
        assert cfg.name == "svc" and abs(cfg.temperature - 0.3) < 1e-9


class TestPipelineApp:
    def test_handlers_execute_in_order(self):
        if answer is None:
            pytest.skip("no answer.py under review")
        app_cls = getattr(answer, "PipelineApp", None)
        if app_cls is None:
            pytest.fail("必须实现 PipelineApp 类")
        app = app_cls()
        app.register_handler(lambda x: x + 1)
        app.register_handler(lambda x: x * 10)
        results = app.run(2)
        assert list(results) == [3, 20], f"应按注册顺序执行并收集结果: {results}"

    def test_empty_pipeline(self):
        """边界条件: 无handler"""
        if answer is None:
            pytest.skip("no answer.py under review")
        app_cls = getattr(answer, "PipelineApp", None)
        assert list(app_cls().run("x")) == []


class TestMonitor:
    def test_counter_increments(self):
        if answer is None:
            pytest.skip("no answer.py under review")
        mon_cls = getattr(answer, "Monitor", None)
        if mon_cls is None:
            pytest.fail("必须实现 Monitor 类")
        mon = mon_cls()
        mon.record("request")
        mon.record("request")
        mon.record("error")
        assert int(mon.count("request")) == 2
        assert int(mon.count("error")) == 1
        assert int(mon.count("missing")) == 0, "未记录事件计数应为0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
