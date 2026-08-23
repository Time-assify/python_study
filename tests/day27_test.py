# Day 27 Tests: 目标检测实战 (PyTorch, 合成数据，不训练大模型)
#
# answer.py 必须实现（接口约定）:
# - DetectionDataset(num_samples=8)   __len__/__getitem__ 返回 (image_tensor, target_dict)
#   target_dict 至少包含 "boxes"(m,4) 与 "labels"(m,)
# - average_precision(pred_boxes, pred_scores, gt_boxes, iou_thr=0.5) -> float
#   完美匹配应返回1.0
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
    obj = getattr(answer, name, None)
    if obj is None:
        pytest.fail(f"必须实现 {name}")
    return obj


@requires_torch
class TestDetectionDataset:
    def test_len_and_item_structure(self):
        ds_cls = _require("DetectionDataset")
        ds = ds_cls(num_samples=6)
        assert len(ds) == 6
        img, target = ds[0]
        assert "boxes" in target and "labels" in target, f"target缺少键: {list(target.keys())}"
        boxes = target["boxes"]
        assert len(boxes.shape) == 2 and boxes.shape[1] >= 4

    def test_box_coords_valid(self):
        """边界条件: xyxy坐标必须 x1<x2, y1<y2"""
        ds_cls = _require("DetectionDataset")
        _img, target = ds_cls(4)[0]
        for b in target["boxes"]:
            b = [float(v) for v in b[:4]]
            assert b[0] < b[2] and b[1] < b[3], f"非法box坐标: {b}"


class TestAveragePrecision:
    def _require_ap(self):
        return _require("average_precision")

    def test_perfect_predictions(self):
        ap = self._require_ap()
        gt = [[0.0, 0.0, 10.0, 10.0], [20.0, 20.0, 30.0, 30.0]]
        val = float(ap(gt.copy(), [1.0, 0.9], gt, 0.5))
        assert abs(val - 1.0) < 1e-6, f"完美预测AP应为1.0，得到{val}"

    def test_no_match_low_ap(self):
        """预测框全部偏离 → AP接近0"""
        ap = self._require_ap()
        gt = [[0.0, 0.0, 10.0, 10.0]]
        bad = [[100.0, 100.0, 110.0, 110.0]]
        val = float(ap(bad, [0.95], gt, 0.5))
        assert val <= 0.5, f"完全不匹配AP应很低，得到{val}"

    def test_empty_gt(self):
        """边界条件: 无GT时返回0或抛出明确异常"""
        ap = self._require_ap()
        try:
            val = float(ap([[0, 0, 1, 1]], [0.9], [], 0.5))
            assert val == 0.0
        except (ValueError, ZeroDivisionError):
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
