# Day 19 Tests: ResNet残差网络 (PyTorch)
#
# answer.py 必须实现（接口约定）:
# - ResidualBlock(channels) -> nn.Module   输出shape与输入shape一致（x + F(x)）
# - SimpleResNet(num_classes=10) -> nn.Module  含至少2个残差块，forward (B,1,28,28)->(B,num_classes)
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
class TestResidualBlock:
    def test_shape_preserved(self):
        """核心性质: 残差块不改变特征图尺寸"""
        block_cls = _require("ResidualBlock")
        block = block_cls(16)
        x = torch.randn(2, 16, 14, 14)
        out = block(x)
        assert tuple(out.shape) == tuple(x.shape), f"shape应保持: {tuple(out.shape)}"

    def test_is_not_identity(self):
        """skip connection存在但F(x)非零"""
        block_cls = _require("ResidualBlock")
        block = block_cls(8)
        with torch.no_grad():
            for p in block.parameters():
                p.add_(0.01)
        x = torch.zeros(1, 8, 6, 6)
        out = block(x)
        assert not torch.allclose(out, x), "输出应包含F(x)分支的贡献"

    def test_gradient_through_shortcut(self):
        """梯度必须能通过shortcut回传"""
        block_cls = _require("ResidualBlock")
        block = block_cls(4)
        x = torch.randn(1, 4, 5, 5, requires_grad=True)
        out = block(x).sum()
        out.backward()
        assert x.grad is not None and float(x.grad.abs().sum()) > 0


@requires_torch
class TestSimpleResNet:
    def test_contains_multiple_blocks(self):
        model_cls = _require("SimpleResNet")
        model = model_cls(num_classes=10)
        block_cls = answer.ResidualBlock
        n_blocks = sum(1 for m in model.modules() if isinstance(m, block_cls))
        assert n_blocks >= 2, f"至少2个残差块，找到{n_blocks}"

    def test_forward_shape(self):
        model_cls = _require("SimpleResNet")
        model = model_cls(num_classes=10)
        out = model(torch.randn(2, 1, 28, 28))
        assert tuple(out.shape) == (2, 10), f"输出shape错误: {tuple(out.shape)}"

    def test_quick_training_step(self):
        """小数据快速训练验证"""
        model_cls = _require("SimpleResNet")
        model = model_cls(num_classes=3)
        crit = nn.CrossEntropyLoss()
        opt = torch.optim.SGD(model.parameters(), lr=0.01)
        x = torch.randn(4, 1, 28, 28)
        y = torch.tensor([0, 1, 2, 1])
        losses = []
        for _ in range(5):
            opt.zero_grad()
            loss = crit(model(x), y)
            loss.backward()
            opt.step()
            losses.append(float(loss))
        assert all(l == l for l in losses), "loss不能为NaN"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
