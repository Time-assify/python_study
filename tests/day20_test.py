# Day 20 Tests: CIFAR图像分类 (PyTorch, 无需下载数据集)
#
# answer.py 必须实现（接口约定）:
# - CIFARNet(num_classes=10) -> nn.Module   forward (B,3,32,32)->(B,num_classes)
# - accuracy(outputs, labels) -> float      logits与标签的top-1准确率
# - confusion_matrix(preds, labels, num_classes) -> ndarray (num_classes,num_classes)
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
    import numpy as np
except ImportError:
    torch = None
    np = None

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
class TestModel:
    def test_forward_shape(self):
        model_cls = _require("CIFARNet")
        out = model_cls(num_classes=10)(torch.randn(2, 3, 32, 32))
        assert tuple(out.shape) == (2, 10), f"CIFAR输入应为(B,3,32,32): {tuple(out.shape)}"

    def test_overfit_tiny_batch(self):
        """小数据快速训练验证: 16个固定样本上loss应明显下降"""
        model_cls = _require("CIFARNet")
        model = model_cls(num_classes=4)
        crit = nn.CrossEntropyLoss()
        opt = torch.optim.SGD(model.parameters(), lr=0.05)
        x = torch.randn(16, 3, 32, 32)
        y = torch.arange(16) % 4
        losses = []
        for _ in range(30):
            opt.zero_grad()
            loss = crit(model(x), y)
            loss.backward()
            opt.step()
            losses.append(float(loss))
        assert losses[-1] < losses[0] * 0.9, f"过拟合小样本失败: {losses[0]:.3f}->{losses[-1]:.3f}"


@requires_torch
class TestMetrics:
    def test_accuracy_perfect_and_half(self):
        acc = _require("accuracy")
        outputs = torch.tensor([
            [5.0, 0.0],   # pred 0
            [0.0, 5.0],   # pred 1
            [5.0, 0.0],   # pred 0
            [0.0, 5.0],   # pred 1
        ])
        labels = torch.tensor([0, 1, 0, 1])
        assert abs(float(acc(outputs, labels)) - 1.0) < 1e-6, "完美预测acc应=1"

        labels2 = torch.tensor([1, 1, 0, 0])
        assert abs(float(acc(outputs, labels2)) - 0.0) < 1e-6

    def test_confusion_matrix_values(self):
        cm_fn = _require("confusion_matrix")
        preds = np.array([0, 1, 1, 2])
        labels = np.array([0, 1, 0, 2])
        cm = cm_fn(preds, labels, 3)
        assert cm.shape == (3, 3)
        assert int(cm[0][0]) == 1 and int(cm[1][1]) == 1 and int(cm[2][2]) == 1
        assert int(cm[0][1]) == 1, "label0被预测成1的位置应有计数"
        assert int(np.asarray(cm).sum()) == 4

    def test_accuracy_mismatched_lengths(self):
        """错误处理: 长度不一致应报错"""
        acc = _require("accuracy")
        with pytest.raises((ValueError, RuntimeError, IndexError)):
            acc(torch.tensor([[1.0, 0.0]]), torch.tensor([0, 1]))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
