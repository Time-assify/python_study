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


@requires_torch
@pytest.mark.skill("pytorch.cnn", "pytorch.optimizer", "pytorch.training_loop")
class TestTrainingSmoke:
    """训练能力冒烟（审核新增）：搭好的网络必须能真正学起来"""

    def test_train_reduces_loss(self):
        """固定小批次30步SGD后loss应明显下降"""
        model_cls = _require("SimpleCNN")
        model = model_cls(num_classes=3)
        crit = nn.CrossEntropyLoss()
        opt = torch.optim.SGD(model.parameters(), lr=0.05)
        x = torch.randn(4, 1, 28, 28)
        y = torch.tensor([0, 1, 2, 0])
        first_loss = float(crit(model(x), y))
        for _ in range(30):
            opt.zero_grad()
            loss = crit(model(x), y)
            loss.backward()
            opt.step()
        final_loss = float(crit(model(x), y))
        assert final_loss < first_loss * 0.9, \
            f"训练冒烟失败: 初始{first_loss:.3f} -> 最终{final_loss:.3f}"

    def test_optimizer_step_updates_params(self):
        """一次backward+step后参数必须发生变化"""
        model_cls = _require("SimpleCNN")
        model = model_cls(num_classes=3)
        snap = [p.detach().clone() for p in model.parameters()]
        crit = nn.CrossEntropyLoss()
        opt = torch.optim.SGD(model.parameters(), lr=0.1)
        x = torch.randn(4, 1, 28, 28)
        y = torch.tensor([0, 1, 2, 0])
        crit(model(x), y).backward()
        opt.step()
        changed = any(
            not torch.equal(p.detach(), s)
            for p, s in zip(model.parameters(), snap)
        )
        assert changed, "optimizer.step()后参数未更新"


@requires_torch
@pytest.mark.skill("pytorch.optimizer", "pytorch.lr_scheduler", "pytorch.training_loop")
class TestTrainingAPI:
    """完整训练闭环API（P0-2）: 优化器分发 / 调度器 / epoch级mini-batch训练"""

    def test_build_optimizer_dispatch(self):
        build_optimizer = _require("build_optimizer")
        params = [torch.nn.Parameter(torch.randn(2))]
        sgd = build_optimizer(params, "sgd", lr=0.1)
        adam = build_optimizer(params, "adam", lr=0.001)
        assert isinstance(sgd, torch.optim.SGD), "name='sgd'应返回SGD"
        assert isinstance(adam, torch.optim.Adam), "name='adam'应返回Adam"

    def test_build_optimizer_invalid(self):
        build_optimizer = _require("build_optimizer")
        params = [torch.nn.Parameter(torch.randn(2))]
        with pytest.raises(ValueError):
            build_optimizer(params, "rmsprop", lr=0.1)
        with pytest.raises(ValueError):
            build_optimizer(params, "sgd", lr=-0.1)

    def test_step_lr_decays(self):
        step_lr = _require("step_lr")
        opt = torch.optim.SGD([torch.nn.Parameter(torch.randn(1))], lr=1.0)
        sched = step_lr(opt, step_size=2, gamma=0.5)
        base_lr = opt.param_groups[0]["lr"]
        for _ in range(2):
            opt.step()
            sched.step()
        after = opt.param_groups[0]["lr"]
        assert after < base_lr, f"两个周期后学习率应衰减: {base_lr} -> {after}"
        assert abs(after - base_lr * 0.5) < 1e-8

    def test_train_one_epoch_matches_manual_avg(self):
        """lr=0时参数不变，epoch平均loss应等于手工逐batch前向的均值"""
        train_one_epoch = _require("train_one_epoch")
        torch.manual_seed(0)
        model = torch.nn.Linear(4, 2)
        x = torch.randn(8, 4)
        y = torch.randint(0, 2, (8,))
        loss_fn = nn.CrossEntropyLoss()
        opt = torch.optim.SGD(model.parameters(), lr=0.0)  # 冻结参数
        returned = float(train_one_epoch(model, x, y, opt, loss_fn, batch_size=4))
        with torch.no_grad():
            expected = (loss_fn(model(x[:4]), y[:4]) + loss_fn(model(x[4:]), y[4:])) / 2
        assert returned == pytest.approx(float(expected), rel=1e-4), \
            f"epoch平均loss错误: 返回{returned}, 期望{float(expected)}"

    def test_train_one_epoch_tail_batch(self):
        """边界: 样本数不整除batch_size时尾批正常处理"""
        train_one_epoch = _require("train_one_epoch")
        model = torch.nn.Linear(4, 2)
        x = torch.randn(7, 4)
        y = torch.randint(0, 2, (7,))
        out = train_one_epoch(model, x, y,
                              torch.optim.SGD(model.parameters(), lr=0.01),
                              nn.CrossEntropyLoss(), batch_size=3)
        assert out >= 0.0 and out == out, "尾批场景应返回有限非负loss"


@requires_torch
@pytest.mark.skill("pytorch.dataloader", "evaluation.accuracy", "pytorch.training_loop")
class TestFullPipeline:
    """P0-2完整闭环: Dataset→DataLoader→CNN→Loss→Optimizer→Backward→loop→Validation"""

    def _loaders(self):
        from torch.utils.data import DataLoader, TensorDataset
        torch.manual_seed(7)
        x = torch.randn(32, 1, 28, 28)
        y = torch.randint(0, 3, (32,))
        train = DataLoader(TensorDataset(x[:24], y[:24]), batch_size=8, shuffle=False)
        val = DataLoader(TensorDataset(x[24:], y[24:]), batch_size=8, shuffle=False)
        return train, val

    def test_report_structure_and_ranges(self):
        fit = _require("fit_classifier")
        model_cls = _require("SimpleCNN")
        model = model_cls(num_classes=3)
        train, val = self._loaders()
        report = fit(model, train, val, epochs=2, lr=0.05)
        assert isinstance(report, dict)
        for key in ("train_loss", "val_loss", "val_acc"):
            assert key in report, f"训练报告缺少键: {key}"
        assert report["train_loss"] >= 0 and report["train_loss"] == report["train_loss"]
        assert report["val_loss"] >= 0 and report["val_loss"] == report["val_loss"]
        assert 0.0 <= report["val_acc"] <= 1.0

    def test_train_loss_matches_manual_when_lr_zero(self):
        """lr=0冻结参数时, 返回的train_loss应等于手工逐batch前向均值(确定性验证)"""
        fit = _require("fit_classifier")
        from torch.utils.data import DataLoader, TensorDataset
        torch.manual_seed(1)
        x, y = torch.randn(8, 1, 28, 28), torch.randint(0, 3, (8,))
        loader = DataLoader(TensorDataset(x, y), batch_size=4, shuffle=False)
        model = _require("SimpleCNN")(num_classes=3)
        loss_fn = nn.CrossEntropyLoss()
        report = fit(model, loader, loader, epochs=1, lr=0.0)
        with torch.no_grad():
            expected = sum(
                float(loss_fn(model(bx), by)) for bx, by in loader
            ) / len(loader)
        assert report["train_loss"] == pytest.approx(expected, rel=1e-4), \
            f"平均loss口径错误: 返回{report['train_loss']}, 期望{expected}"

    def test_learning_actually_happens(self):
        """可分数据上数个epoch后val_acc应显著高于随机猜测"""
        from torch.utils.data import DataLoader, TensorDataset
        fit = _require("fit_classifier")
        torch.manual_seed(3)
        n = 24
        x = torch.randn(n, 1, 28, 28)
        y = (x[:, 0, :, :].mean(dim=(1, 2)) > 0).long()
        train = DataLoader(TensorDataset(x[:16], y[:16]), batch_size=8)
        val = DataLoader(TensorDataset(x[16:], y[16:]), batch_size=4)
        model = _require("SimpleCNN")(num_classes=2)
        report = fit(model, train, val, epochs=10, lr=0.08)
        assert report["val_acc"] >= 0.75, \
            f"简单可分任务10个epoch后val_acc应>=0.75, 得到{report['val_acc']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
