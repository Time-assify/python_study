# Day 20 Tests: CIFAR图像分类 + Phase2毕业小项目 (PyTorch, 无需下载数据集)
#
# answer.py 必须实现（接口约定）:
# - CIFARNet(num_classes=10) -> nn.Module   forward (B,3,32,32)->(B,num_classes)
# - accuracy(outputs, labels) -> float      logits与标签的top-1准确率
# - confusion_matrix(preds, labels, num_classes) -> ndarray (num_classes,num_classes)
# - build_dataset_loaders(batch_size=8) -> (train_loader, val_loader)
#     合成(B,3,32,32)张量数据（禁止下载CIFAR10），两类可分，划分互斥
# - train_and_validate(model, train_loader, val_loader, epochs=3, lr=0.05) -> dict
#     返回{'train_loss','val_loss','val_acc'}；validation阶段不得更新参数
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
@pytest.mark.skill("cv.classification", "metrics.confusion_matrix")
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
@pytest.mark.skill("cv.classification", "metrics.confusion_matrix")
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

        labels2 = torch.tensor([1, 0, 1, 0])
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


@requires_torch
@pytest.mark.skill("pytorch.dataset", "pytorch.dataloader", "pytorch.training_loop",
                   "cv.classification")
class TestMiniCapstone:
    """P1-4: Phase2毕业小项目——Dataset/DataLoader/CNN/Training/Validation全链串联"""

    def test_build_dataset_loaders(self):
        build = _require("build_dataset_loaders")
        train_loader, val_loader = build(batch_size=8)
        names = (type(train_loader).__name__, type(val_loader).__name__)
        assert all("DataLoader" in n for n in names), f"应返回两个DataLoader: {names}"
        train_batches = list(train_loader)
        bx, by = train_batches[0]
        assert tuple(bx.shape[1:]) == (3, 32, 32), f"样本应为(3,32,32): {tuple(bx.shape[1:])}"
        total = sum(len(bx) for bx, _ in train_loader) + sum(len(bx) for bx, _ in val_loader)
        assert total >= 40, f"合成数据规模过小: {total}"

    def test_end_to_end_training(self):
        """端到端: 数据→CIFARNet→训练→验证, 报告三指标齐全且合法"""
        build = _require("build_dataset_loaders")
        train_and_validate = _require("train_and_validate")
        model_cls = _require("CIFARNet")
        model = model_cls(num_classes=2)
        train_loader, val_loader = build(batch_size=8)
        report = train_and_validate(model, train_loader, val_loader,
                                    epochs=2, lr=0.05)
        assert isinstance(report, dict)
        for key in ("train_loss", "val_loss", "val_acc"):
            assert key in report, f"报告缺少{key}"
        assert 0.0 <= float(report["val_acc"]) <= 1.0
        assert float(report["train_loss"]) >= 0 and float(report["train_loss"]) == report["train_loss"]

    def test_learning_happens_on_separable_synthetic(self):
        """可分合成数据上训练后val_acc应显著高于随机(2类=>>0.5)"""
        build = _require("build_dataset_loaders")
        train_and_validate = _require("train_and_validate")
        model_cls = _require("CIFARNet")
        model = model_cls(num_classes=2)
        train_loader, val_loader = build(batch_size=8)
        report = train_and_validate(model, train_loader, val_loader,
                                    epochs=6, lr=0.08)
        assert float(report["val_acc"]) >= 0.7, \
            f"可分合成任务6个epoch后val_acc应>=0.7, 得到{report['val_acc']}"

    def test_confusion_integrates_with_model(self):
        """混淆矩阵与模型输出打通: 矩阵元素和==样本数"""
        build = _require("build_dataset_loaders")
        cm_fn = _require("confusion_matrix")
        model_cls = _require("CIFARNet")
        model = model_cls(num_classes=2)
        _, val_loader = build(batch_size=8)
        bx, by = next(iter(val_loader))
        with torch.no_grad():
            preds = model(bx).argmax(dim=1)
        cm = np.asarray(cm_fn(preds, by, num_classes=2))
        assert int(cm.sum()) == len(by), f"混淆矩阵元素和应等于样本数: {cm.sum()} vs {len(by)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
