# Day 23 Tests: 图像分类数据集与训练闭环 (PyTorch, 合成图像)
#
# answer.py 必须实现（接口约定）:
# - make_color_samples(n_per_class=12) -> (samples, labels)
#     合成HWC整数数组(16,16,3)两类可分彩色图; labels为0/1
# - ImagesDataset(samples, labels)   Dataset: __getitem__返回(CHW float[0~1]张量, int标签)
# - cnn_baseline(num_classes=2) -> nn.Module   小型卷积基线(适配16x16输入)
# - train_classifier(model, train_loader, val_loader, epochs=5,
#                    lr=0.05, save_path=None) -> dict
#     返回{'train_loss','val_loss','val_acc'}; 给出save_path时把最优val权重
#     torch.save到该路径
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
    from torch.utils.data import DataLoader
except ImportError:
    torch = None
    nn = None
    DataLoader = None

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


def _dataset():
    make = _require("make_color_samples")
    samples, labels = make(n_per_class=6)
    ds_cls = _require("ImagesDataset")
    return ds_cls(samples, labels)


@requires_torch
@pytest.mark.skill("cv.image_tensor", "pytorch.dataset", "cv.classification")
class TestImagesDataset:
    def test_len_and_item_structure(self):
        ds = _dataset()
        assert len(ds) == 12, f"6+6应有12个样本: {len(ds)}"
        x, y = ds[0]
        assert torch.is_tensor(x), "特征应为张量"
        assert tuple(x.shape) == (3, 16, 16), f"应为CHW=(3,16,16): {tuple(x.shape)}"
        assert int(y) in (0, 1)

    def test_values_normalized(self):
        """基础能力: HWC 0~255 整数必须转成 CHW float 0~1"""
        ds = _dataset()
        x, _ = ds[3]
        assert x.dtype == torch.float32
        assert float(x.min()) >= 0.0 and float(x.max()) <= 1.0


@requires_torch
@pytest.mark.skill("cv.classification", "evaluation.accuracy",
                   "pytorch.training_loop", "pytorch.checkpoint", "pytorch.dataloader")
class TestTrainClassifier:
    def _loaders(self):
        ds = _dataset()
        n = len(ds)
        train = DataLoader(ds, batch_size=4, shuffle=False)
        # 用同一数据集的后半部分做验证(合成数据, 重点在管线而非泛化)
        val = DataLoader(torch.utils.data.Subset(ds, range(n // 2, n)), batch_size=4)
        model = _require("cnn_baseline")(num_classes=2)
        return model, train, val

    def test_report_and_model_file(self, tmp_path):
        fit = _require("train_classifier")
        model, train, val = self._loaders()
        path = str(tmp_path / "best.pt")
        report = fit(model, train, val, epochs=2, lr=0.05, save_path=path)
        assert isinstance(report, dict)
        for key in ("train_loss", "val_loss", "val_acc"):
            assert key in report, f"报告缺少{key}"
        assert 0.0 <= float(report["val_acc"]) <= 1.0
        assert float(report["train_loss"]) >= 0
        import os
        assert os.path.exists(path), "给了save_path就必须落盘最优权重"
        blob = torch.load(path)
        assert isinstance(blob, dict) and len(blob) > 0, "保存内容应是state_dict"

    def test_separable_task_reaches_high_val_acc(self):
        """强可分彩色两类, 8个epoch后val_acc应>=0.9——证明真的会训练"""
        fit = _require("train_classifier")
        model, train, val = self._loaders()
        report = fit(model, train, val, epochs=8, lr=0.1)
        assert float(report["val_acc"]) >= 0.9, \
            f"可分任务8个epoch后val_acc应>=0.9, 得到{report['val_acc']}"

    def test_saved_weights_reproduce_val_acc(self):
        """加载save_path权重到同构新模型, val_acc必须复现报告值"""
        fit = _require("train_classifier")
        model, train, val = self._loaders()
        import tempfile, os
        path = os.path.join(tempfile.mkdtemp(), "best.pt")
        report = fit(model, train, val, epochs=2, lr=0.05, save_path=path)
        fresh = _require("cnn_baseline")(num_classes=2)
        fresh.load_state_dict(torch.load(path))
        fresh.eval()
        correct = total = 0
        with torch.no_grad():
            for bx, by in val:
                preds = fresh(bx).argmax(dim=1)
                correct += int((preds == by).sum())
                total += len(by)
        acc = correct / total
        assert acc == pytest.approx(float(report["val_acc"]), abs=1e-6), \
            f"恢复权重后acc应复现: {acc} vs {report['val_acc']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
