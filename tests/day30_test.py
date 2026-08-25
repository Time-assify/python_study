# Day 30 Tests: CV阶段综合项目 (PyTorch, 合成数据)
#
# Phase 2/3毕业项目: 数据→模型→训练→评价→结果展示 全链串联。
#
# answer.py 必须实现（接口约定）:
# - TrainConfig(epochs:int, lr:float, batch_size:int, num_classes:int=2,
#               out_path:str="best.pt")   dataclass
#     含 from_dict(d) / to_dict(); 缺必需字段抛 KeyError/TypeError
# - save_config(config, path) / load_config(path)   yaml持久化roundtrip
# - make_loaders(n_train=32, n_val=8, batch_size=8) -> (train_loader, val_loader)
#     合成可分两类(3,32,32)张量数据; 两集合互斥; 禁止下载真实数据集
# - build_model(num_classes=2) -> nn.Module    小型CNN
# - run_pipeline(config) -> dict
#     按config执行: 建数据 → 建模型 → 训练 → 验证 → 保存最优权重到config.out_path
#     返回{'train_loss','val_loss','val_acc','model_path'}
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
    import torch
    import torch.nn as nn
except ImportError:
    torch = None
    nn = None


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


@pytest.mark.skill("engineering.config")
class TestTrainConfig:
    def test_roundtrip(self):
        cls = _require("TrainConfig")
        cfg = cls(epochs=3, lr=0.05, batch_size=8, num_classes=2,
                  out_path="best.pt")
        d = cfg.to_dict()
        assert d["epochs"] == 3 and abs(d["lr"] - 0.05) < 1e-9
        cfg2 = cls.from_dict(d)
        assert cfg2.epochs == cfg.epochs and cfg2.batch_size == cfg.batch_size

    def test_missing_key_raises(self):
        """错误处理: 缺少必需字段"""
        cls = _require("TrainConfig")
        with pytest.raises((KeyError, TypeError)):
            cls.from_dict({"epochs": 3})

    def test_yaml_persistence(self, tmp_path):
        import yaml
        cls = _require("TrainConfig")
        save_config = getattr(answer, "save_config", None)
        load_config = getattr(answer, "load_config", None)
        if save_config is None or load_config is None:
            pytest.fail("必须实现 save_config()/load_config()")
        path = str(tmp_path / "cfg.yaml")
        save_config(cls(epochs=2, lr=0.1, batch_size=4), path)
        cfg = load_config(path)
        assert cfg.epochs == 2 and abs(cfg.lr - 0.1) < 1e-9
        assert yaml.safe_load(open(path, encoding="utf-8"))["epochs"] == 2


def _make_loaders():
    return _require("make_loaders")(n_train=32, n_val=8, batch_size=8)


def _build_model():
    return _require("build_model")(num_classes=2)


@pytest.mark.skipif(torch is None, reason="PyTorch未安装（环境问题）")
@pytest.mark.skill("application.pipeline", "cv.classification",
                   "evaluation.accuracy", "pytorch.training_loop", "pytorch.checkpoint")
class TestRunPipeline:
    def _config(self, tmp_path, **kw):
        cls = _require("TrainConfig")
        base = dict(epochs=2, lr=0.05, batch_size=8, num_classes=2,
                    out_path=str(tmp_path / "best.pt"))
        base.update(kw)
        return cls(**base)

    def test_loaders_structure(self):
        train, val = _make_loaders()
        bx, by = next(iter(train))
        assert tuple(bx.shape[1:]) == (3, 32, 32), f"样本应(3,32,32): {tuple(bx.shape[1:])}"
        assert set(by.tolist()) <= {0, 1}
        total = sum(len(bx) for bx, _ in train) + sum(len(bx) for bx, _ in val)
        assert total == 40, f"32训练+8验证: {total}"

    def test_pipeline_report_and_artifact(self, tmp_path):
        """端到端: 报告三指标齐全 + 最优权重确实落盘"""
        run = _require("run_pipeline")
        cfg = self._config(tmp_path)
        report = run(cfg)
        assert isinstance(report, dict)
        for key in ("train_loss", "val_loss", "val_acc", "model_path"):
            assert key in report, f"流水线报告缺少{key}"
        import os
        assert os.path.exists(str(report.get("model_path", cfg.out_path))), \
            "run_pipeline必须把最优权重保存到out_path"
        assert 0.0 <= float(report["val_acc"]) <= 1.0
        assert float(report["train_loss"]) >= 0

    def test_saved_model_reproduces_val_acc(self, tmp_path):
        """加载产物权重到同构新模型, val_acc必须复现报告值——结果可展示的底线"""
        run = _require("run_pipeline")
        make = _require("make_loaders")
        cfg = self._config(tmp_path, epochs=3, lr=0.08)
        report = run(cfg)
        fresh = _build_model()
        fresh.load_state_dict(torch.load(report["model_path"]))
        fresh.eval()
        _, val = make(n_train=32, n_val=8, batch_size=8)
        correct = total = 0
        with torch.no_grad():
            for bx, by in val:
                preds = fresh(bx).argmax(dim=1)
                correct += int((preds == by).sum())
                total += len(by)
        acc = correct / total
        assert acc == pytest.approx(float(report["val_acc"]), abs=1e-6), \
            f"恢复权重后acc应复现报告值: {acc} vs {report['val_acc']}"

    def test_separable_data_learns(self):
        """可分合成数据上, 数个epoch后val_acc应显著高于随机"""
        run = _require("run_pipeline")
        cls = _require("TrainConfig")
        import tempfile, os
        cfg = cls(epochs=6, lr=0.08, batch_size=8, num_classes=2,
                  out_path=os.path.join(tempfile.mkdtemp(), "best.pt"))
        report = run(cfg)
        assert float(report["val_acc"]) >= 0.7, \
            f"可分任务6个epoch后val_acc应>=0.7, 得到{report['val_acc']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
