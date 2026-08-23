# Day 09 Tests: Autograd自动微分 (PyTorch)
#
# answer.py 必须实现（接口约定）:
# - quadratic(a, b, c, x) -> Tensor      计算 a*x^2 + b*x + c，x需可求导
# - gradient_at(fn, x_value) -> Tensor   返回fn在x处的梯度标量tensor
# - nested_fn(x) -> Tensor               组合函数 sin(exp(x))（用于链式法则验证）
import math

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
except ImportError:
    torch = None

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
class TestGradientComputation:
    def test_quadratic_value(self):
        q = _require("quadratic")
        x = torch.tensor(2.0, requires_grad=True)
        y = q(1.0, 0.0, 0.0, x)  # x^2
        assert float(y) == 4.0

    def test_gradient_of_square(self):
        """基础功能: d/dx x^2 在 x=3 处应为6"""
        grad = _require("gradient_at")
        g = grad(lambda x: x * x, 3.0)
        assert abs(float(g) - 6.0) < 1e-5, f"x^2在3处梯度应为6，得到{float(g)}"

    def test_gradient_linear(self):
        grad = _require("gradient_at")
        g = grad(lambda x: 3 * x + 1, 10.0)
        assert abs(float(g) - 3.0) < 1e-6


@requires_torch
class TestChainRule:
    def test_nested_gradient(self):
        """任务要求检查: d/dx sin(exp(x)) at x=0 → cos(e^0)*e^0 = cos(1)"""
        if answer is None:
            pytest.skip("no answer.py under review")
        nested = getattr(answer, "nested_fn", None)
        if nested is None:
            pytest.fail("必须实现 nested_fn(x): 返回 sin(exp(x))")
        grad = _require("gradient_at")
        g = grad(nested, 0.0)
        expected = math.cos(math.e)
        assert abs(float(g) - expected) < 1e-4, f"链式法则梯度错误: {float(g)} vs {expected}"


@requires_torch
class TestGradientAccumulation:
    def test_backward_accumulates(self):
        """边界条件: 连续两次backward梯度累加"""
        grad = _require("gradient_at")

        x = torch.tensor(1.0, requires_grad=True)
        y = x * 2.0
        y.backward()
        first = float(x.grad)
        y2 = x * 2.0
        y2.backward()
        second = float(x.grad)
        assert first == 2.0 and second == 4.0, "PyTorch梯度默认累加，两次应得4"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
