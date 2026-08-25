# Day 11 Tests: PyTorch Tensor基础（dtype/device/shape/requires_grad/backward）
#
# answer.py 必须实现（接口约定）:
# - tensor_info(t) -> dict            至少包含 shape / dtype / device 三个键
# - to_device(t, device) -> Tensor    把张量移到指定设备并返回
# - grad_of_quadratic(a, b, c, x_value) -> Tensor
#     对 f(x)=a*x^2+b*x+c 在 x=x_value 处求梯度，返回标量Tensor
# - grad_after_two_backwards(x_value) -> float
#     同一叶子张量上两次独立前向+反向后，返回累积梯度值
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
@pytest.mark.skill("pytorch.tensor", "pytorch.tensor_shape")
class TestTensorInfo:
    def test_info_has_three_keys(self):
        tensor_info = _require("tensor_info")
        t = torch.randn(2, 3)
        info = tensor_info(t)
        assert isinstance(info, dict), "tensor_info应返回字典"
        for key in ("shape", "dtype", "device"):
            assert key in info, f"info缺少键: {key}"

    def test_info_values(self):
        tensor_info = _require("tensor_info")
        t = torch.randn(4, 5)
        info = tensor_info(t)
        assert tuple(info["shape"]) == (4, 5), f"shape错误: {info['shape']}"
        assert info["dtype"] == torch.float32, "默认dtype应为float32"
        assert info["device"].type == "cpu"


@requires_torch
@pytest.mark.skill("pytorch.tensor", "pytorch.device")
class TestDeviceMove:
    def test_to_device_cpu(self):
        to_device = _require("to_device")
        t = torch.randn(3)
        moved = to_device(t, torch.device("cpu"))
        assert moved.device.type == "cpu"
        assert torch.equal(moved, t), "移动不应改变数值"

    def test_to_device_accepts_str(self):
        """边界: device参数也接受字符串"""
        to_device = _require("to_device")
        moved = to_device(torch.ones(2), "cpu")
        assert moved.device.type == "cpu"


@requires_torch
@pytest.mark.skill("pytorch.autograd", "pytorch.tensor")
class TestAutogradBasics:
    def test_grad_of_quadratic_known_value(self):
        """f(x)=2x^2+x 在x=3处梯度应为13"""
        fn = _require("grad_of_quadratic")
        g = fn(a=2.0, b=1.0, c=0.0, x_value=3.0)
        assert float(g) == pytest.approx(13.0, abs=1e-5), \
            f"二次函数在x=3的梯度应为13, 得到{float(g)}"

    def test_grad_returns_scalar_tensor(self):
        fn = _require("grad_of_quadratic")
        g = fn(1.0, 0.0, 0.0, 5.0)
        assert torch.is_tensor(g), "应返回Tensor而不是python数值"

    def test_grads_accumulate_over_backwards(self):
        """两次独立forward+backward后梯度应累加: d(3x)/dx 累加为6"""
        fn = _require("grad_after_two_backwards")
        total = float(fn(x_value=7.0))
        assert total == pytest.approx(6.0, abs=1e-5), \
            f"两次backward后梯度应累加为6, 得到{total}"


@requires_torch
@pytest.mark.skill("pytorch.device")
class TestEnvironmentCheck:
    """环境体检：能判断CPU/GPU环境是一等能力"""

    def test_report_structure(self):
        check = _require("check_environment")
        report = check()
        assert isinstance(report, dict)
        for key in ("cuda_available", "device_count", "torch_version", "default_device"):
            assert key in report, f"环境报告缺少键: {key}"

    def test_report_consistency(self):
        """无CUDA时默认设备必须是cpu——这是最常见的环境误判"""
        check = _require("check_environment")
        report = check()
        assert isinstance(report["cuda_available"], bool)
        assert isinstance(report["device_count"], int) and report["device_count"] >= 0
        if not report["cuda_available"]:
            assert report["default_device"] == "cpu", \
                "无CUDA时默认设备必须是cpu"


@requires_torch
@pytest.mark.skill("pytorch.tensor_shape")
class TestShapeDebug:
    def test_compatible_passes(self):
        fn = _require("checked_matmul")
        a, b = torch.randn(2, 3), torch.randn(3, 4)
        assert fn(a, b) is None, "兼容形状应静默通过"

    def test_mismatch_raises_with_both_shapes(self):
        """核心排错能力: 报错信息必须包含两个冲突shape"""
        fn = _require("checked_matmul")
        a, b = torch.randn(2, 3), torch.randn(4, 5)
        with pytest.raises(ValueError) as exc:
            fn(a, b)
        msg = str(exc.value)
        assert "(2, 3)" in msg and "(4, 5)" in msg, \
            f"报错应包含两个shape便于定位: {msg}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
