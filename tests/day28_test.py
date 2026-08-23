# Day 28 Tests: ONNX模型导出 (需要onnx/onnxruntime)
#
# answer.py 必须实现（接口约定）:
# - export_to_onnx(model, dummy_input, path) -> None   torch.onnx.export封装
# - onnx_forward(path, input) -> ndarray               onnxruntime推理
import inspect

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

try:
    import onnx  # noqa
except ImportError:
    onnx = None

try:
    import onnxruntime  # noqa
except ImportError:
    onnxruntime = None

requires_full = pytest.mark.skipif(
    onnx is None or onnxruntime is None or torch is None,
    reason="torch/onnx/onnxruntime未安装（环境问题）"
)


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


@pytest.mark.skill("deployment.onnx")
class TestAPIContract:
    def test_export_signature_has_dynamic_axes(self):
        """任务要求检查: export应支持dynamic_axes参数"""
        if torch is None or answer is None:
            pytest.skip("torch未安装（环境问题）")
        if answer is None:
            pytest.skip("no answer.py under review")
        export = getattr(answer, "export_to_onnx", None)
        if export is None:
            pytest.fail("必须实现 export_to_onnx()")
        sig = inspect.signature(export)
        assert "dynamic_axes" in sig.parameters or any(
            p.kind == p.VAR_KEYWORD for p in sig.parameters.values()
        ), "export_to_onnx应支持dynamic_axes（动态batch）"


@requires_full
@pytest.mark.skill("deployment.onnx")
class TestExportInference:
    def test_export_creates_file(self, tmp_path):
        export = _require("export_to_onnx")
        model = nn.Linear(4, 2).eval()
        dummy = torch.randn(1, 4)
        path = str(tmp_path / "model.onnx")
        export(model, dummy, path)
        import os
        assert os.path.exists(path), "ONNX文件未生成"
        assert os.path.getsize(path) > 0

    def test_onnx_inference_matches_torch(self, tmp_path):
        """数值一致性: ONNX输出与PyTorch输出接近"""
        export = _require("export_to_onnx")
        forward = _require("onnx_forward")
        model = nn.Linear(4, 2).eval()
        x = torch.randn(2, 4)
        path = str(tmp_path / "m.onnx")
        export(model, x[:1], path)

        out_onnx = forward(path, x.numpy())
        with torch.no_grad():
            out_torch = model(x).numpy()
        diff = abs(out_onnx - out_torch).max()
        assert diff < 1e-4, f"ONNX与PyTorch输出差异过大: {diff}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
