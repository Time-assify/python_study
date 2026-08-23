# Day 21 Tests: 数据增强 (需要torchvision)
#
# answer.py 必须实现（接口约定）:
# - get_train_transform() -> torchvision.transforms.Compose
#   管线中至少包含: RandomHorizontalFlip / RandomCrop / ColorJitter（名称匹配即可）
# - apply_transform(transform, img) -> Tensor   对CHW float tensor应用增强，shape保持(3,H,W)
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

try:
    import torchvision.transforms as T
except ImportError:
    T = None

requires_tv = pytest.mark.skipif(T is None, reason="torchvision未安装（环境问题）")
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


@requires_tv
@pytest.mark.skill("cv.augmentation", "torchvision.transforms")
class TestTransformPipeline:
    def test_returns_compose(self):
        get_train = _require("get_train_transform")
        pipeline = get_train_transform = get_train()
        assert isinstance(pipeline, T.Compose), "应返回transforms.Compose"

    def test_contains_required_ops(self):
        """任务要求检查: 翻转/裁剪/色彩抖动"""
        get_train = _require("get_train_transform")
        names = [type(t).__name__ for t in get_train().transforms]
        joined = " ".join(names)
        for op in ("Flip", "Crop", "Jitter"):
            assert op in joined, f"管线缺少{op}类操作，当前: {names}"

    @requires_torch
    def test_apply_preserves_shape(self):
        get_train = _require("get_train_transform")
        if answer is None:
            pytest.skip("no answer.py under review")
        apply_fn = getattr(answer, "apply_transform", None)
        if apply_fn is None:
            pytest.fail("必须实现 apply_transform()")
        img = torch.rand(3, 32, 32)  # CHW float
        out = apply_fn(get_train(), img)
        assert tuple(out.shape) == (3, 32, 32), f"增强后shape必须保持: {tuple(out.shape)}"

    @requires_torch
    def test_flip_deterministic_with_p1(self):
        """边界条件: p=1的翻转应确定性地改变图像"""
        flip = T.RandomHorizontalFlip(p=1.0)
        img = torch.arange(36, dtype=torch.float32).reshape(1, 6, 6)
        out = flip(img)
        assert not torch.equal(out, img), "p=1时水平翻转必须改变图像"
        assert torch.allclose(out, img.flip(-1)), "翻转结果与tensor.flip(-1)一致"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
