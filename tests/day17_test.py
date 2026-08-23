# Day 17 Tests: 模型保存与加载 (PyTorch)
#
# answer.py 必须实现（接口约定）:
# - save_checkpoint(model, path, epoch=0, optimizer=None) -> None
# - load_checkpoint(path) -> dict  至少包含 'model_state' 和 'epoch'
# - restore_model(model, path) -> model  将checkpoint权重恢复到model
import os

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

requires_torch = pytest.mark.skipif(torch is None, reason="PyTorch未安装（环境问题）")


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


def _tiny_model(seed=0):
    torch.manual_seed(seed)
    return nn.Sequential(nn.Linear(4, 3), nn.ReLU(), nn.Linear(3, 1))


@requires_torch
class TestCheckpoint:
    def test_save_and_load_roundtrip(self, tmp_path):
        save = _require("save_checkpoint")
        load = _require("load_checkpoint")
        model = _tiny_model()
        path = str(tmp_path / "ckpt.pt")
        save(model, path, epoch=7)
        assert os.path.exists(path), "checkpoint文件未创建"

        ckpt = load(path)
        assert "epoch" in ckpt and int(ckpt["epoch"]) == 7, "必须保存并返回epoch"
        state_key = next((k for k in ("model_state", "state_dict", "model") if k in ckpt), None)
        assert state_key is not None, f"checkpoint缺少模型权重键: {list(ckpt.keys())}"

    def test_restore_weights_equal(self, tmp_path):
        """任务要求检查: 恢复后的模型参数与新初始化模型不同、与原模型相同"""
        save = _require("save_checkpoint")
        if answer is None:
            pytest.skip("no answer.py under review")
        restore = getattr(answer, "restore_model", None)
        if restore is None:
            pytest.fail("必须实现 restore_model()")
        model_a = _tiny_model(42)
        path = str(tmp_path / "m.pt")
        save(model_a, path)

        model_b = _tiny_model(999)  # 不同初始化
        w_before = model_b[0].weight.clone()
        model_b = restore(model_b, path)
        assert not torch.equal(model_b[0].weight, w_before), "restore后权重应变化"
        assert torch.equal(model_b[0].weight, model_a[0].weight), "恢复后权重应与原模型一致"

    def test_load_missing_file_raises(self, tmp_path):
        """错误处理: 文件不存在"""
        load = _require("load_checkpoint")
        with pytest.raises((FileNotFoundError, IOError, RuntimeError)):
            load(str(tmp_path / "no_such.pt"))

    def test_resume_epoch_metadata(self, tmp_path):
        """边界条件: checkpoint可恢复训练元信息"""
        save = _require("save_checkpoint")
        load = _require("load_checkpoint")
        model = _tiny_model()
        opt = torch.optim.SGD(model.parameters(), lr=0.01)
        path = str(tmp_path / "c2.pt")
        save(model, path, epoch=12, optimizer=opt)
        ckpt = load(path)
        if isinstance(ckpt, dict) and "optimizer_state" in ckpt or "optimizer" in ckpt:
            pass  # 可选保存optimizer
        assert int(ckpt.get("epoch", -1)) == 12


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
