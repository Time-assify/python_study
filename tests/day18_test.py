# Day 18 Tests: 完整训练流程 (PyTorch)
#
# answer.py 必须实现（接口约定）:
# - train_one_epoch(model, loader, optimizer, loss_fn) -> float   平均训练loss
# - evaluate(model, loader, loss_fn) -> (loss, accuracy)
# - EarlyStopping(patience, min_delta=0.0)  .step(val_loss) -> bool  是否应停止；patience<1抛ValueError
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
    from torch.utils.data import DataLoader, TensorDataset
except ImportError:
    torch = None
    nn = None
    DataLoader = None

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


def _linear_data():
    X = torch.randn(64, 3)
    w = torch.tensor([[2.0], [-1.0], [0.5]])
    y = X @ w
    return DataLoader(TensorDataset(X, y), batch_size=16)


@requires_torch
@pytest.mark.skill("pytorch.training_loop", "evaluation.accuracy")
class TestTrainingLoop:
    def test_train_epoch_returns_loss(self):
        train = _require("train_one_epoch")
        model = nn.Linear(3, 1)
        opt = torch.optim.SGD(model.parameters(), lr=0.05)
        crit = nn.MSELoss()
        loss = train(model, _linear_data(), opt, crit)
        assert isinstance(loss, float) and loss == loss and loss >= 0

    def test_training_converges(self):
        """小数据快速训练验证: 5个epoch后loss显著下降"""
        train = _require("train_one_epoch")
        evaluate = getattr(answer, "evaluate", None)
        model = nn.Linear(3, 1)
        opt = torch.optim.SGD(model.parameters(), lr=0.05)
        crit = nn.MSELoss()
        loader = _linear_data()
        first_loss = train(model, loader, opt, crit)
        for _ in range(4):
            last_loss = train(model, loader, opt, crit)
        assert last_loss < first_loss * 0.8, f"训练应收敛: {first_loss:.4f}->{last_loss:.4f}"


@requires_torch
@pytest.mark.skill("pytorch.training_loop", "evaluation.accuracy")
class TestEvaluation:
    def test_evaluate_accuracy(self):
        evaluate = _require("evaluate")
        # 构造完美可分数据验证accuracy=1
        X = torch.tensor([[10.0], [-10.0], [9.0], [-9.0]])
        y = torch.tensor([1.0, 0.0, 1.0, 0.0])
        model = nn.Linear(1, 1)

        class FixedModel(torch.nn.Module):
            def forward(self, x):
                return x

        out = evaluate(FixedModel(), DataLoader(TensorDataset(X, y), batch_size=2),
                       nn.BCEWithLogitsLoss())
        loss, acc = out
        assert float(acc) == 1.0, f"正负样本应100%准确，得到{acc}"


@pytest.mark.skill("pytorch.training_loop", "evaluation.accuracy")
class TestEarlyStopping:
    def test_stops_after_patience(self):
        if answer is None:
            pytest.skip("no answer.py under review")
        es_cls = getattr(answer, "EarlyStopping", None)
        if es_cls is None:
            pytest.fail("必须实现 EarlyStopping 类")
        es = es_cls(patience=2)
        flags = [es.step(1.0), es.step(0.9), es.step(0.95), es.step(0.94)]
        assert flags[0] is False or flags[0] == False, "第一次不应停止"
        assert any(bool(f) for f in flags[2:]), "连续不改善patience次后应停止"

    def test_improvement_resets(self):
        """边界条件: 改善会重置计数"""
        if answer is None:
            pytest.skip("no answer.py under review")
        es_cls = getattr(answer, "EarlyStopping", None)
        if es_cls is None:
            pytest.fail("必须实现 EarlyStopping 类")
        es = es_cls(patience=2)
        es.step(1.0)
        es.step(1.2)      # 不改善1次
        stopped = es.step(0.5)  # 改善→重置→False
        assert not bool(stopped), "有改善时不应停止"

    def test_invalid_patience(self):
        """错误处理: patience<1"""
        if answer is None:
            pytest.skip("no answer.py under review")
        es_cls = getattr(answer, "EarlyStopping", None)
        if es_cls is None:
            pytest.fail("必须实现 EarlyStopping 类")
        with pytest.raises(ValueError):
            es_cls(patience=0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
