# Day 15 Tests: 训练Debug能力 (PyTorch)
#
# 目标: 不是训练更大模型, 而是会找问题。
#
# answer.py 必须实现（接口约定）:
# - assert_matmul_compatible(a, b)                形状兼容静默通过；
#                                                 不兼容抛ValueError且消息包含两个shape
# - check_gradient_flow(model, x, y, loss_fn=None) -> dict
#     至少含 has_gradients(bool) / num_params(int) / max_abs_grad(float>=0)
# - is_eval_deterministic(model, x, mode="eval") -> bool
#     指定模式下连续两次前向是否完全一致（Dropout/BN行为差异检测）
# - diagnose_loss_history(losses) -> dict
#     至少含 trend("decreasing"/"flat"/"increasing") 与 suggestions(list)
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
@pytest.mark.skill("pytorch.tensor_shape", "pytorch.training_step")
class TestShapeCheck:
    def test_compatible_shapes_pass(self):
        fn = _require("assert_matmul_compatible")
        assert fn(torch.randn(8, 3), torch.randn(3, 2)) is None

    def test_mismatch_raises_with_shapes_in_message(self):
        """核心排错能力: 报错必须能定位冲突的两个shape"""
        fn = _require("assert_matmul_compatible")
        a, b = torch.randn(6, 5), torch.randn(2, 7)
        with pytest.raises(ValueError) as exc:
            fn(a, b)
        msg = str(exc.value)
        assert "(6, 5)" in msg and "(2, 7)" in msg, \
            f"错误信息应包含两个shape: {msg}"


@requires_torch
@pytest.mark.skill("pytorch.autograd", "pytorch.training_step")
class TestGradientInspection:
    def test_fresh_model_has_gradients(self):
        check = _require("check_gradient_flow")
        model = nn.Linear(4, 2)
        report = check(model, torch.randn(8, 4), torch.randint(0, 2, (8,)))
        assert isinstance(report, dict)
        for key in ("has_gradients", "num_params", "max_abs_grad"):
            assert key in report, f"缺少键: {key}"
        assert report["has_gradients"] is True, "正常反向传播后参数应有梯度"
        assert report["num_params"] >= 2
        assert isinstance(report["max_abs_grad"], float) and report["max_abs_grad"] >= 0

    def test_zero_input_still_reports(self):
        """边界: 全零输入也应产出结构完整的报告(梯度可为0但不能崩)"""
        check = _require("check_gradient_flow")
        model = nn.Linear(4, 2)
        with torch.no_grad():
            model.weight.zero_()
            model.bias.fill_(1.0)
        report = check(model, torch.zeros(4, 4), torch.randint(0, 2, (4,)))
        assert "has_gradients" in report and "max_abs_grad" in report


@requires_torch
@pytest.mark.skill("pytorch.training_step")
class TestTrainEvalDetection:
    def test_dropout_model_deterministic_in_eval(self):
        fn = _require("is_eval_deterministic")
        model = nn.Sequential(nn.Dropout(p=0.5), nn.Linear(8, 2))
        assert fn(model, torch.randn(64, 8), mode="eval") is True, \
            "eval模式下Dropout模型应输出确定"

    def test_dropout_model_stochastic_in_train(self):
        """train模式的随机性必须能被检出——这是train/eval区别的实证"""
        fn = _require("is_eval_deterministic")
        model = nn.Sequential(nn.Dropout(p=0.9), nn.Linear(64, 2))
        assert fn(model, torch.randn(128, 64), mode="train") is False, \
            "train模式下高比例Dropout应输出不确定"

    def test_plain_linear_always_deterministic(self):
        fn = _require("is_eval_deterministic")
        model = nn.Linear(4, 2)
        assert fn(model, torch.randn(16, 4), mode="train") is True


@requires_torch
@pytest.mark.skill("pytorch.training_loop", "pytorch.training_step")
class TestLossDiagnosis:
    def test_decreasing_detected(self):
        fn = _require("diagnose_loss_history")
        report = fn([1.0, 0.7, 0.5, 0.35])
        assert report["trend"] == "decreasing"

    def test_flat_flagged_with_suggestions(self):
        """loss不下降原因排查——本日核心"""
        fn = _require("diagnose_loss_history")
        report = fn([0.69, 0.69, 0.69, 0.69])
        assert report["trend"] == "flat"
        assert len(report["suggestions"]) >= 1, "flat必须给出排查建议"
        assert all(isinstance(s, str) and s for s in report["suggestions"])

    def test_increasing_flagged_with_suggestions(self):
        fn = _require("diagnose_loss_history")
        report = fn([0.5, 0.8, 1.4, 2.0])
        assert report["trend"] == "increasing"
        assert len(report["suggestions"]) >= 1

    def test_short_history_handled(self):
        """边界: 少于两个点无法判趋势, 不应崩溃"""
        fn = _require("diagnose_loss_history")
        report = fn([0.5])
        assert isinstance(report, dict) and "trend" in report


@requires_torch
@pytest.mark.skill("pytorch.debugging")
class TestCaseTriage:
    """P0-3: 症状→原因→修复 三段式分诊落地"""

    REQUIRED_FIX_KEYWORDS = {
        "shape_mismatch": ("shape",),
        "grad_not_cleared": ("zero_grad",),
        "missing_eval_switch": ("eval",),
        "loss_not_decreasing": ("learning",),  # learning rate / learning rate schedule
    }

    def test_known_cases_dispatch(self):
        fn = _require("debug_training_issue")
        for case in self.REQUIRED_FIX_KEYWORDS:
            report = fn(case)
            assert isinstance(report, dict), f"{case}应返回字典"
            for key in ("issue", "symptom", "fix"):
                assert key in report, f"{case}诊断缺少'{key}'"
                assert isinstance(report[key], str) and report[key].strip(), \
                    f"{case}.{key}必须非空"
            assert report["issue"] == case, f"issue应回显病例名: {report['issue']}"

    def test_fix_contains_actionable_keyword(self):
        """修复建议必须命中关键动作词——空话式建议不合格"""
        fn = _require("debug_training_issue")
        for case, keywords in self.REQUIRED_FIX_KEYWORDS.items():
            report = fn(case)
            fix = report["fix"].lower()
            assert any(kw in fix for kw in keywords), \
                f"{case}的fix应包含{keywords}之一: {report['fix']}"

    def test_unknown_case_raises(self):
        fn = _require("debug_training_issue")
        with pytest.raises(ValueError):
            fn("alien_invasion")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
