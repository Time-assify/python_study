# Day 13 Tests: CNN卷积神经网络 (PyTorch)
#
# answer.py 必须实现（接口约定）:
# - SimpleCNN(num_classes=10) -> nn.Module
#   接受 (B,1,28,28) 灰度图，经 Conv2d(3x3,padding=1)+ReLU+MaxPool2d(2) 后接全连接，
#   输出 (B,num_classes)
# - count_conv_layers(model) -> int   卷积层数量>=1
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
@pytest.mark.skill("pytorch.cnn", "pytorch.tensor_shape")
class TestCNNStructure:
    def test_has_conv_layer(self):
        count_conv = _require("count_conv_layers")
        model_cls = _require("SimpleCNN")
        n = int(count_conv(model_cls()))
        assert n >= 1, f"CNN至少要有一个卷积层，得到{n}"

    def test_pooling_exists(self):
        model_cls = _require("SimpleCNN")
        model = model_cls()
        has_pool = any(isinstance(m, (nn.MaxPool2d, nn.AvgPool2d)) for m in model.modules())
        assert has_pool, "结构中应包含池化层"


@requires_torch
@pytest.mark.skill("pytorch.cnn", "pytorch.tensor_shape")
class TestForward:
    def test_output_shape(self):
        """forward shape: (B,1,28,28) -> (B,num_classes)"""
        model_cls = _require("SimpleCNN")
        model = model_cls(num_classes=10)
        out = model(torch.randn(2, 1, 28, 28))
        assert tuple(out.shape) == (2, 10), f"输出shape错误: {tuple(out.shape)}"

    def test_batch_size_one(self):
        """边界条件: batch=1"""
        model_cls = _require("SimpleCNN")
        out = model_cls(num_classes=5)(torch.randn(1, 1, 28, 28))
        assert tuple(out.shape) == (1, 5)

    def test_backward_flows(self):
        """小数据快速训练验证: loss有限且可反向传播"""
        model_cls = _require("SimpleCNN")
        model = model_cls(num_classes=3)
        crit = nn.CrossEntropyLoss()
        x = torch.randn(4, 1, 28, 28)
        y = torch.tensor([0, 1, 2, 0])
        loss = crit(model(x), y)
        assert torch.isfinite(loss), "loss必须有限"
        loss.backward()
        grads = [p.grad for p in model.parameters() if p.grad is not None]
        assert len(grads) > 0, "反向传播后应有梯度"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
