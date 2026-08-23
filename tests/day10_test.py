# Day 10 Tests: nn.Module构建块 (PyTorch)
#
# answer.py 必须实现（接口约定）:
# - MLP(in_features, hidden, out_features) -> nn.Module   Linear-ReLU-Linear
# - count_parameters(model) -> int                        可训练参数总数
# - build_activation(name) -> nn.Module                   'relu'/'sigmoid'/'tanh'；未知名抛ValueError
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
class TestMLP:
    def test_forward_shape(self):
        mlp_cls = _require("MLP")
        model = mlp_cls(4, 8, 2)
        out = model(torch.randn(5, 4))
        assert tuple(out.shape) == (5, 2), f"输出shape错误: {tuple(out.shape)}"

    def test_parameter_count(self):
        """任务要求检查: 参数量 = in*h+h + h*out+out (含bias)"""
        mlp_cls = _require("MLP")
        count = _require("count_parameters")
        model = mlp_cls(4, 8, 2)
        expected = 4 * 8 + 8 + 8 * 2 + 2
        got = int(count(model))
        assert got == expected, f"参数量应为{expected}，得到{got}"

    def test_training_reduces_loss(self):
        """小数据快速训练验证"""
        mlp_cls = _require("MLP")
        model = mlp_cls(1, 16, 1)
        opt = torch.optim.SGD(model.parameters(), lr=0.05)
        crit = nn.MSELoss()
        X = torch.linspace(-1, 1, 32).unsqueeze(1)
        y = (X * 2).clone()
        first = last = None
        for i in range(60):
            opt.zero_grad()
            loss = crit(model(X), y)
            loss.backward()
            opt.step()
            if first is None:
                first = float(loss)
            last = float(loss)
        assert last < first, "训练后loss应下降"
        assert last == last, "loss不能是NaN"


@requires_torch
class TestActivation:
    def test_relu_and_sigmoid(self):
        build = _require("build_activation")
        relu = build("relu")
        sig = build("sigmoid")
        x = torch.tensor([-1.0, 0.0, 2.0])
        assert torch.equal(relu(x), torch.tensor([0.0, 0.0, 2.0]))
        s = sig(x)
        assert ((s > 0) & (s < 1)).all(), "sigmoid输出必须在(0,1)"

    def test_unknown_name_raises(self):
        """错误处理: 未知激活名"""
        build = _require("build_activation")
        with pytest.raises(ValueError):
            build("gelu_max_pro")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
