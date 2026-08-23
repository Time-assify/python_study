# Day 16 Tests: TensorBoard可视化 (PyTorch)
#
# answer.py 必须实现（接口约定）:
# - get_writer(logdir) -> SummaryWriter
# - log_metrics(writer, step, metrics)   metrics为dict {name: value}
# - close_writer(writer)
import os

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
    from torch.utils.tensorboard import SummaryWriter
except ImportError:
    torch = None
    SummaryWriter = None

requires_tb = pytest.mark.skipif(
    SummaryWriter is None,
    reason="torch.utils.tensorboard不可用（环境问题，需tensorboard包）"
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


def _find_event_file(logdir):
    for root, _dirs, files in os.walk(str(logdir)):
        for f in files:
            if f.startswith("events.out.tfevents"):
                return os.path.join(root, f)
    return None


@requires_tb
class TestTensorBoard:
    def test_get_writer_creates_dir(self, tmp_path):
        get_writer = _require("get_writer")
        logdir = tmp_path / "runs"
        writer = get_writer(str(logdir))
        try:
            assert isinstance(writer, SummaryWriter), f"应返回SummaryWriter，得到{type(writer)}"
            assert logdir.exists(), "logdir目录应被创建"
        finally:
            close = getattr(answer, "close_writer", None)
            if callable(close):
                close(writer)
            else:
                writer.close()

    def test_scalar_logging_writes_event_file(self, tmp_path):
        """基础功能+任务要求检查: 标量落盘"""
        get_writer = _require("get_writer")
        if answer is None:
            pytest.skip("no answer.py under review")
        log_metrics = getattr(answer, "log_metrics", None)
        if log_metrics is None:
            pytest.fail("必须实现 log_metrics()")
        logdir = tmp_path / "runs2"
        writer = get_writer(str(logdir))
        try:
            log_metrics(writer, 0, {"loss": 1.5})
            log_metrics(writer, 1, {"loss": 1.2, "acc": 0.6})
            writer.flush()
        finally:
            writer.close()
        assert _find_event_file(logdir) is not None, "未找到tfevents文件"

    def test_close_idempotent(self, tmp_path):
        """边界条件: 重复close不应报错"""
        get_writer = _require("get_writer")
        writer = get_writer(str(tmp_path / "runs3"))
        writer.close()
        writer.close()  # 第二次close不应抛异常


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
