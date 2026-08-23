# Day 12 Tests: 优化器 (PyTorch)
#
# answer.py 必须实现（接口约定）:
# - build_optimizer(params, name, lr) -> torch.optim.Optimizer  'sgd'/'adam'；未知名抛ValueError；lr<=0抛ValueError
# - step_lr(optimizer, step_size, gamma=0.1) -> 学习率调度器
# - train_steps(model, data, target, optimizer, loss_fn, steps=20) -> float  返回最终loss
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


def _quadratic_model():
    model = nn.Linear(1, 1, bias=False)
    with torch.no_grad():
        model.weight.fill_(4.0)
    return model


@requires_torch
class TestOptimizerFactory:
    def test_build_sgd_adam(self):
        build = _require("build_optimizer")
        p = [nn.Parameter(torch.tensor([1.0]))]
        assert isinstance(build(p, "sgd", 0.1), torch.optim.Optimizer)
        assert isinstance(build(p, "adam", 0.01), torch.optim.Optimizer)

    def test_invalid_lr_raises(self):
        """错误处理: lr<=0"""
        build = _require("build_optimizer")
        p = [nn.Parameter(torch.tensor([1.0]))]
        with pytest.raises(ValueError):
            build(p, "sgd", 0.0)

    def test_unknown_name_raises(self):
        build = _require("build_optimizer")
        p = [nn.Parameter(torch.tensor([1.0]))]
        with pytest.raises(ValueError):
            build(p, "momentum_max", 0.1)


@requires_torch
class TestTraining:
    def _run(self, name, lr, steps=30):
        build = _require("build_optimizer")
        model = _quadratic_model()
        opt = build(model.parameters(), name, lr)
        crit = nn.MSELoss()
        x = torch.zeros(8, 1)
        y = torch.zeros(8, 1)
        losses = []
        for _ in range(steps):
            opt.zero_grad()
            loss = crit(model(x), y)
            loss.backward()
            opt.step()
            losses.append(float(loss))
        return losses

    def test_sgd_decreases_loss(self):
        losses = self._run("sgd", 0.1)
        assert losses[-1] < losses[0], f"SGD训练后loss应下降: {losses[0]:.3f}->{losses[-1]:.3f}"

    def test_adam_decreases_loss(self):
        losses = self._run("adam", 0.5)
        assert losses[-1] < losses[0], "Adam训练后loss应下降"


@requires_torch
class TestScheduler:
    def test_lr_decays_after_step_size(self):
        step_lr = _require("step_lr")
        build = _require("build_optimizer")
        model = _quadratic_model()
        opt = build(model.parameters(), "sgd", 1.0)
        sched = step_lr(opt, 2, gamma=0.1)
        lrs = []
        for _ in range(5):
            lrs.append(opt.param_groups[0]["lr"])
            opt.step()
            sched.step()
        # epoch0,1: 1.0; 之后衰减
        assert abs(lrs[0] - 1.0) < 1e-9
        assert lrs[-1] < lrs[0], f"调度器应降低学习率: {lrs}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
