# Day 22 Tests: 迁移学习 (PyTorch, 无需下载预训练权重)
#
# answer.py 必须实现（接口约定）:
# - freeze_backbone(model) -> (model, frozen_count)   冻结除最后线性层外的所有参数
# - unfreeze_all(model) -> model                      全部解冻
# - extract_features(model, x) -> Tensor              no_grad下提取倒数第二层特征
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
        pytest.fail(f"必须实现 {name}")
    return fn


def _backbone():
    """测试用的迷你backbone: features(2层Conv)+classifier(1层Linear)"""
    return nn.Sequential(
        nn.Sequential(nn.Conv2d(3, 4, 3, padding=1), nn.ReLU(),
                      nn.Conv2d(4, 4, 3, padding=1), nn.ReLU()),
        nn.Flatten(),
        nn.Linear(4 * 8 * 8, 10),
    )


@requires_torch
@pytest.mark.skill("transfer_learning", "parameter_freezing")
class TestFreezing:
    def test_freeze_locks_params(self):
        freeze = _require("freeze_backbone")
        model = _backbone()
        _, frozen = freeze(model)
        trainable_after = sum(p.requires_grad for p in model.parameters())
        assert trainable_after < len(list(model.parameters())), "冻结后可训练参数应减少"
        # classifier（最后一个Linear）必须保持可训练
        last_linear = [m for m in model.modules() if isinstance(m, nn.Linear)][-1]
        assert all(p.requires_grad for p in last_linear.parameters()), "分类头不应被冻结"

    def test_frozen_params_get_no_grad(self):
        """冻结参数在训练中不更新"""
        freeze = _require("freeze_backbone")
        model = _backbone()
        freeze(model)
        before = [p.clone() for p in model[0].parameters()]
        opt = torch.optim.SGD([p for p in model.parameters() if p.requires_grad], lr=0.1)
        x = torch.randn(2, 3, 8, 8)
        loss = model(x).sum()
        loss.backward()
        opt.step()
        for b, p in zip(before, model[0].parameters()):
            assert torch.equal(b, p), "被冻结的backbone权重不应更新"


@requires_torch
@pytest.mark.skill("transfer_learning", "parameter_freezing")
class TestUnfreeze:
    def test_unfreeze_all(self):
        unfreeze = _require("unfreeze_all")
        freeze = _require("freeze_backbone")
        model = _backbone()
        freeze(model)
        model = unfreeze(model)
        assert all(p.requires_grad for p in model.parameters()), "unfreeze后所有参数可训练"

    def test_freeze_unfreeze_roundtrip(self):
        """边界条件: 反复冻结/解冻状态正确"""
        freeze = _require("freeze_backbone")
        unfreeze = _require("unfreeze_all")
        model = _backbone()
        for _ in range(3):
            freeze(model)
            model = unfreeze(model)
        assert all(p.requires_grad for p in model.parameters())


@requires_torch
@pytest.mark.skill("transfer_learning", "parameter_freezing")
class TestFeatureExtraction:
    def test_features_no_grad(self):
        if answer is None:
            pytest.skip("no answer.py under review")
        extract = getattr(answer, "extract_features", None)
        if extract is None:
            pytest.fail("必须实现 extract_features()")
        model = _backbone().eval()
        x = torch.randn(1, 3, 8, 8)
        feats = extract(model, x)
        assert not (torch.is_tensor(feats) and feats.requires_grad), "特征提取必须no_grad"
        assert torch.is_tensor(feats) and feats.shape[0] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
