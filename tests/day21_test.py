# Day 21 Tests: 图像张量与数据增强 (需要torchvision)
#
# answer.py 必须实现（接口约定）:
# - get_train_transform() -> torchvision.transforms.Compose
#   管线中至少包含: RandomHorizontalFlip / RandomCrop / ColorJitter（名称匹配即可）
# - apply_transform(transform, img) -> Tensor   对CHW float tensor应用增强，shape保持(3,H,W)
# - image_to_tensor(img_hwc) -> Tensor          HWC(0~255) -> CHW float32(0~1)
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


@requires_torch
@pytest.mark.skill("cv.image_tensor", "cv.transform")
class TestImageTensor:
    """P0-1: 图片三形态 HWC数组 → CHW张量 的标准转换"""

    def _sample(self):
        # 6x4的RGB图, 三通道取值可区分
        img = [[[r * 40, g * 60, b * 80] for g in range(4)] for r in range(6)]
        # 上面每个像素是[R,G,B]混合; 为区分通道, 改为通道常量图:
        return [[[(r % 256), (g % 256), ((r + g) % 256)] for g in range(4)]
                for r in range(6)]

    def test_shape_and_range(self):
        fn = _require("image_to_tensor")
        img = self._sample()  # H=6, W=4, C=3
        t = fn(img)
        assert tuple(t.shape) == (3, 6, 4), f"应为CHW=(3,6,4): {tuple(t.shape)}"
        assert t.dtype == torch.float32
        assert float(t.min()) >= 0.0 and float(t.max()) <= 1.0, "应归一化到[0,1]"

    def test_channel_order_preserved(self):
        """转置不能搞错通道与空间轴"""
        fn = _require("image_to_tensor")
        img = self._sample()
        t = fn(img)
        # 第0通道应等于原HWC的第0通道除以255
        orig_c0 = torch.tensor([[row[c][0] for c in range(4)] for row in img],
                               dtype=torch.float32) / 255.0
        assert torch.allclose(t[0], orig_c0, atol=1e-6), "R通道被错误置换"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
