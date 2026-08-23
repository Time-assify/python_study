# Day 15 Tests: GPU训练 (PyTorch)
#
# answer.py 必须实现（接口约定）:
# - get_device() -> torch.device        cuda可用返回cuda，否则cpu
# - move_to_device(obj, device)         将模型或tensor移到指定device并返回
# - train_step(model, x, y, device) -> float  单步训练，返回CPU上的float loss
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


@requires_torch
class TestDeviceSelection:
    def test_get_device_type(self):
        get_device = _require("get_device")
        dev = get_device()
        assert isinstance(dev, torch.device), f"应返回torch.device，得到{type(dev)}"
        assert dev.type in ("cuda", "cpu")

    def test_move_tensor(self):
        """数据传输: tensor移到device"""
        move = _require("move_to_device")
        dev = torch.device("cpu")
        t = move(torch.randn(3, 3), dev)
        assert t.device.type == "cpu"

    def test_move_model(self):
        """模型上device"""
        move = _require("move_to_device")
        model = nn.Linear(4, 2)
        model = move(model, torch.device("cpu"))
        assert all(p.device.type == "cpu" for p in model.parameters())


@requires_torch
class TestTrainStep:
    def test_train_step_returns_float(self):
        """CPU回退路径必须可运行（无GPU也能通过）"""
        train_step = _require("train_step")
        model = nn.Linear(4, 1)
        dev = torch.device("cpu")
        x = torch.randn(8, 4)
        y = torch.randn(8, 1)
        loss = train_step(model, x, y, dev)
        assert isinstance(loss, float), f"应返回float，得到{type(loss)}"
        assert loss == loss and loss >= 0, "loss必须是非NaN非负数"

    def test_loss_decreases_over_steps(self):
        """小数据快速训练验证"""
        train_step = _require("train_step")
        model = nn.Linear(4, 1)
        opt = torch.optim.SGD(model.parameters(), lr=0.05)
        # 若train_step内部自建optimizer则忽略外部opt——这里只验证多次调用收敛趋势
        x = torch.randn(16, 4)
        w_true = torch.tensor([[1.0], [-2.0], [0.5], [3.0]])
        y = x @ w_true
        losses = [train_step(model, x, y, torch.device("cpu")) for _ in range(25)]
        assert losses[-1] <= losses[0] + 1e-9, f"loss应下降或持平: {losses[0]:.4f}->{losses[-1]:.4f}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
