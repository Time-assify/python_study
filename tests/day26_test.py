# Day 26 Tests: YOLO目标检测基础 (纯数学实现，无需torchvision)
#
# answer.py 必须实现（接口约定）:
# - gen_anchors(grid_size, anchor_sizes, aspect_ratios) -> Tensor/ndarray (N,4)
#   每行 [cx, cy, w, h]（相对坐标0~1）；N = grid_size^2 * len(anchor_sizes)*len(aspect_ratios)
# - iou(box_a, box_b) -> float    boxes为[x1,y1,x2,y2]
# - nms(boxes, scores, iou_threshold) -> list[int]   保留框索引，按分数降序抑制重叠
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


@pytest.mark.skill("detection.anchor", "detection.iou", "detection.nms")
class TestAnchors:
    def test_anchor_count_and_range(self):
        gen = _require("gen_anchors")
        anchors = gen(3, [4, 8], [1.0])
        n = len(list(anchors))
        assert n == 9 * 2 * 1, f"锚框数应为grid²×sizes×ratios=18，得到{n}"

    def test_anchor_coords_normalized(self):
        """边界条件: 坐标必须在[0,1]"""
        gen = _require("gen_anchors")
        vals = [float(v) for row in gen(2, [5], [1.0]) for v in row]
        assert all(0.0 <= v <= 1.0 for v in vals), f"锚框坐标必须归一化: {vals[:6]}"


@pytest.mark.skill("detection.anchor", "detection.iou", "detection.nms")
class TestIoU:
    def test_identical_boxes(self):
        iou = _require("iou")
        b = [0.0, 0.0, 10.0, 10.0]
        assert abs(float(iou(b, b)) - 1.0) < 1e-6

    def test_disjoint_boxes(self):
        iou = _require("iou")
        assert float(iou([0, 0, 5, 5], [100, 100, 110, 110])) == 0.0

    def test_half_overlap(self):
        """边界条件: 一半重叠 IoU = 交集/并集"""
        iou = _require("iou")
        val = float(iou([0, 0, 10, 10], [5, 0, 15, 10]))
        expected = 50.0 / 150.0
        assert abs(val - expected) < 1e-6, f"IoU应为{expected:.4f}，得到{val}"


@pytest.mark.skill("detection.anchor", "detection.iou", "detection.nms")
class TestNMS:
    def test_nms_suppresses_overlap(self):
        nms = _require("nms")
        boxes = [
            [0, 0, 10, 10],
            [1, 1, 11, 11],    # 与box0高度重叠 → 应被抑制
            [50, 50, 60, 60],  # 独立 → 保留
        ]
        scores = [0.9, 0.8, 0.7]
        keep = list(nms(boxes, scores, 0.5))
        assert set(keep) == {0, 2}, f"应保留{{0,2}}，得到{set(keep)}"

    def test_nms_keeps_distinct_with_low_threshold_effect(self):
        """低重叠不抑制"""
        nms = _require("nms")
        keep = list(nms([[0, 0, 5, 5], [20, 20, 25, 25]], [0.9, 0.85], 0.5))
        assert sorted(keep) == [0, 1]

    def test_nms_empty_input(self):
        """边界条件: 空输入"""
        nms = _require("nms")
        assert list(nms([], [], 0.5)) == []

    def test_invalid_threshold_raises(self):
        """错误处理: 阈值必须在[0,1]"""
        nms = _require("nms")
        with pytest.raises(ValueError):
            nms([[0, 0, 1, 1]], [0.9], 1.5)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
