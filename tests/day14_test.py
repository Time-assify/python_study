# Day 14 Tests: BatchNorm/Dropout正则化 (PyTorch)
#
# answer.py 必须实现（接口约定）:
# - NetWithReg(in_features, num_classes, p_drop=0.5) -> nn.Module
#   至少包含一个 nn.BatchNorm1d 和一个 nn.Dropout
# - forward输出 (B, num_classes)
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
