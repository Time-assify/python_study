# Day 08 Tests: Tensor基础操作 (PyTorch)
#
# answer.py 必须实现（接口约定）:
# - create_tensor(data) -> torch.FloatTensor   dtype=float32
# - reshape_tensor(t, shape) -> Tensor         shape为tuple
# - tensor_stats(t) -> (mean, std)             两个float
# - index_last(t) -> Tensor                    取最后一行/最后一个元素
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
@pytest.mark.skill("pytorch.tensor")
class TestTensorCreation:
    def test_create_tensor_dtype(self):
        create = _require("create_tensor")
        t = create([[1.0, 2.0], [3.0, 4.0]])
        assert torch.is_tensor(t)
        assert t.dtype == torch.float32, f"dtype应为float32，得到{t.dtype}"

    def test_create_tensor_values(self):
        create = _require("create_tensor")
        t = create([1, 2, 3])
        assert t.tolist() == [1.0, 2.0, 3.0]


@requires_torch
@pytest.mark.skill("pytorch.tensor")
class TestTensorOps:
    def test_reshape_preserves_elements(self):
        reshape = _require("reshape_tensor")
        t = torch.arange(12, dtype=torch.float32)
        out = reshape(t, (3, 4))
        assert out.shape == (3, 4)
        assert out.numel() == 12

    def test_reshape_invalid_shape_raises(self):
        """错误处理: 元素数不匹配应报错"""
        reshape = _require("reshape_tensor")
        t = torch.arange(12, dtype=torch.float32)
        with pytest.raises((RuntimeError, ValueError)):
            reshape(t, (5, 5))


@requires_torch
@pytest.mark.skill("pytorch.tensor")
class TestTensorStats:
    def test_stats_values(self):
        stats = _require("tensor_stats")
        t = torch.tensor([1.0, 2.0, 3.0, 4.0])
        mean, std = stats(t)
        assert abs(float(mean) - 2.5) < 1e-6

    def test_index_last(self):
        idx = _require("index_last")
        t = torch.tensor([[1.0, 2.0], [3.0, 9.0]])
        last = idx(t)
        assert float(torch.as_tensor(last).flatten()[-1]) == 9.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
