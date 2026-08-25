# Day 12 Tests: Dataset/DataLoader (PyTorch)
#
# answer.py 必须实现（接口约定）:
# - SimpleDataset(data, labels, transform=None)  实现 __len__/__getitem__，返回(x, label)
# - make_loader(dataset, batch_size, shuffle=False) -> DataLoader
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
    from torch.utils.data import Dataset, DataLoader
except ImportError:
    torch = None
    Dataset = None
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


def _make_dataset():
    cls = _require("SimpleDataset")
    data = [float(i) for i in range(10)]
    labels = [i % 2 for i in range(10)]
    return cls(data, labels)


@requires_torch
@pytest.mark.skill("pytorch.dataset", "pytorch.dataloader")
class TestDataset:
    def test_is_dataset_subclass(self):
        ds_cls = _require("SimpleDataset")
        assert issubclass(ds_cls, Dataset), "必须继承torch.utils.data.Dataset"

    def test_len_and_getitem(self):
        """基础功能"""
        ds = _make_dataset()
        assert len(ds) == 10
        x, y = ds[0]
        assert float(x) == 0.0 and int(y) == 0

    def test_getitem_types(self):
        """任务要求检查: 返回(tensor, label)对"""
        ds = _make_dataset()
        item = ds[5]
        assert isinstance(item, (tuple, list)) and len(item) == 2


@requires_torch
@pytest.mark.skill("pytorch.dataset", "pytorch.dataloader")
class TestDataLoader:
    def test_batches_count(self):
        make_loader = _require("make_loader")
        loader = make_loader(_make_dataset(), batch_size=4)
        assert isinstance(loader, DataLoader)
        batches = list(loader)
        assert len(batches) == 3, f"10条/batch4应有3个batch(4+4+2)，得到{len(batches)}"

    def test_last_batch_smaller(self):
        """边界条件: 最后一个batch可以不足"""
        make_loader = _require("make_loader")
        batches = list(make_loader(_make_dataset(), batch_size=4))
        assert len(batches[-1][0]) == 2

    def test_transform_applied(self):
        """transform参数应作用在每个样本上"""
        ds_cls = _require("SimpleDataset")
        ds = ds_cls([1.0] * 6, [0] * 6, transform=lambda x: x * 100.0)
        x, _ = ds[0]
        assert abs(float(x) - 100.0) < 1e-6, "transform未被应用"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
