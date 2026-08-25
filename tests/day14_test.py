# Day 14 Tests: BatchNorm/Dropout正则化 + Validation (PyTorch)
#
# answer.py 必须实现（接口约定）:
# - NetWithReg(in_features, num_classes, p_drop=0.5) -> nn.Module
#   至少包含一个 nn.BatchNorm1d 和一个 nn.Dropout
# - forward输出 (B, num_classes)
# - train_validation_split(n, val_ratio=0.2) -> (train_idx, val_idx)
#     验证集数量为max(1, int(n*val_ratio))；两个索引集互斥且并集覆盖0..n-1
# - evaluate_accuracy(model, x, y) -> float
#     在(x, y)上计算top-1准确率（0到1的float）
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
@pytest.mark.skill("pytorch.batchnorm", "pytorch.dropout")
class TestStructure:
    def test_contains_batchnorm_and_dropout(self):
        cls = _require("NetWithReg")
        model = cls(16, 4)
        has_bn = any(isinstance(m, (nn.BatchNorm1d, nn.BatchNorm2d)) for m in model.modules())
        has_drop = any(isinstance(m, nn.Dropout) for m in model.modules())
        assert has_bn, "必须包含BatchNorm层"
        assert has_drop, "必须包含Dropout层"


@requires_torch
@pytest.mark.skill("pytorch.batchnorm", "pytorch.dropout")
class TestBehavior:
    def _model(self):
        return _require("NetWithReg")(8, 2, p_drop=0.5)

    def test_forward_shape(self):
        out = self._model()(torch.randn(6, 8))
        assert tuple(out.shape) == (6, 2)

    def test_batchnorm_normalizes(self):
        """基础功能: BN后batch均值应接近0"""
        model = self._model().eval()
        x = torch.randn(64, 8) * 5 + 3
        # 找到第一个BN层单独验证其归一化能力
        bn = next(m for m in model.modules() if isinstance(m, nn.BatchNorm1d))
        with torch.no_grad():
            out = bn(x)
        assert out.mean(dim=0).abs().max() < 1e-4, "BatchNorm应将均值归零"

    def test_dropout_train_vs_eval(self):
        """核心行为: train模式有随机性，eval模式确定性"""
        model = self._model()
        model.train()
        x = torch.randn(32, 8)
        a, b = model(x), model(x)
        assert not torch.allclose(a, b), "train模式下Dropout应引入随机性"
        model.eval()
        with torch.no_grad():
            c, d = model(x), model(x)
        assert torch.allclose(c, d), "eval模式下输出必须确定"

    def test_invalid_p_raises(self):
        """错误处理: p不在[0,1]"""
        cls = _require("NetWithReg")
        with pytest.raises(ValueError):
            cls(8, 2, p_drop=1.5)


@requires_torch
@pytest.mark.skill("evaluation.accuracy", "pytorch.training_loop")
class TestValidationSplit:
    """P0-3: train/validation split 与验证准确率"""

    def test_split_sizes_default_ratio(self):
        split = _require("train_validation_split")
        train_idx, val_idx = split(10, val_ratio=0.2)
        assert len(val_idx) == 2, f"10条按0.2应划出2条验证, 得到{len(val_idx)}"
        assert len(train_idx) == 8

    def test_split_min_one_val(self):
        """边界: n很小导致int(n*ratio)=0时至少保留1条验证"""
        split = _require("train_validation_split")
        _, val_idx = split(3, val_ratio=0.1)
        assert len(val_idx) >= 1, "验证集至少要有1条样本"

    def test_split_disjoint_and_covering(self):
        split = _require("train_validation_split")
        train_idx, val_idx = split(12, val_ratio=0.25)
        train_set, val_set = set(map(int, train_idx)), set(map(int, val_idx))
        assert not (train_set & val_set), "train与val索引必须互斥"
        assert train_set | val_set == set(range(12)), "两集合并集必须覆盖全部样本"

    def test_evaluate_accuracy_known_values(self):
        evaluate_accuracy = _require("evaluate_accuracy")
        model = torch.nn.Linear(4, 2)
        with torch.no_grad():
            model.weight.copy_(torch.tensor([[1.0, 0, 0, 0], [-1.0, 0, 0, 0]]))
            model.bias.zero_()
        x = torch.tensor([[1.0, 0, 0, 0],
                          [1.0, 0, 0, 0],
                          [-1.0, 0, 0, 0],
                          [1.0, 0, 0, 0]])
        y = torch.tensor([0, 1, 0, 0])
        acc = float(evaluate_accuracy(model, x, y))
        assert acc == pytest.approx(0.75), f"3/4正确应为0.75, 得到{acc}"

    def test_evaluate_accuracy_range(self):
        evaluate_accuracy = _require("evaluate_accuracy")
        model = torch.nn.Linear(4, 2)
        acc = float(evaluate_accuracy(model, torch.randn(16, 4),
                                      torch.randint(0, 2, (16,))))
        assert 0.0 <= acc <= 1.0, "准确率必须在[0,1]区间"


@requires_torch
@pytest.mark.skill("evaluation.accuracy", "pytorch.training_loop")
class TestLossCurve:
    """loss curve: 会记录并解读训练曲线是评估能力的一部分"""

    def test_curve_length_and_finite(self):
        record = _require("record_loss_curve")
        torch.manual_seed(0)
        model = torch.nn.Linear(4, 2)
        x = torch.randn(64, 4)
        y = (x[:, 0] > 0).long()
        curve = record(model, x, y, epochs=8, lr=0.1)
        assert isinstance(curve, list) and len(curve) == 8
        assert all(isinstance(v, float) and v >= 0 and v == v for v in curve), \
            "曲线每项应为有限非负float"

    def test_curve_decreases_overall(self):
        """可分数据上整条曲线应下降（首>尾），这是loss curve的核心判读"""
        record = _require("record_loss_curve")
        torch.manual_seed(42)
        model = torch.nn.Linear(4, 2)
        x = torch.randn(128, 4)
        y = ((x[:, 0] + x[:, 1]) > 0).long()
        curve = record(model, x, y, epochs=15, lr=0.2)
        assert curve[-1] < curve[0] * 0.7, \
            f"15个epoch后应明显下降: 首{curve[0]:.3f} 尾{curve[-1]:.3f}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
