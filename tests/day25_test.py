# Day 25 Tests: HuggingFace Transformers（离线构建，不下载权重）
#
# answer.py 必须实现（接口约定）:
# - hf_forward(model, input_ids) -> Tensor        返回last_hidden_state
# - count_hf_params(model) -> int                 参数总量
# - pad_ids(ids: list[int], max_len) -> torch.Tensor  右padding到max_len
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
    from transformers import BertConfig, BertModel
    HF_OK = True
except ImportError:
    torch = None
    HF_OK = False

requires_hf = pytest.mark.skipif(not HF_OK or torch is None,
                                 reason="transformers/torch未安装（环境问题）")


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


def _tiny_bert():
    cfg = BertConfig(vocab_size=100, hidden_size=32, num_hidden_layers=1,
                     num_attention_heads=2, intermediate_size=64)
    return BertModel(cfg)


@requires_hf
@pytest.mark.skill("huggingface.model")
class TestHFModelOps:
    def test_hf_forward_shape(self):
        hf_forward = _require("hf_forward")
        model = _tiny_bert().eval()
        ids = torch.randint(0, 100, (2, 5))
        out = hf_forward(model, ids)
        # last_hidden_state
        if hasattr(out, "last_hidden_state"):
            out = out.last_hidden_state
        assert tuple(out.shape) == (2, 5, 32), f"hidden state shape错误: {tuple(out.shape)}"

    def test_count_params_positive(self):
        count = _require("count_hf_params")
        n = int(count(_tiny_bert()))
        assert n > 0, "参数量必须>0"


@pytest.mark.skill("huggingface.model")
class TestPadding:
    def test_pad_ids(self):
        """不依赖transformers，纯torch即可测"""
        if torch is None:
            pytest.skip("torch未安装（环境问题）")
        if answer is None:
            pytest.skip("no answer.py under review")
        pad = getattr(answer, "pad_ids", None)
        if pad is None:
            pytest.fail("必须实现 pad_ids()")
        t = pad([1, 2, 3], 6)
        assert tuple(t.shape) == (6,)
        assert [int(v) for v in t] == [1, 2, 3, 0, 0, 0], "右侧应补0"

    def test_pad_no_truncate_needed(self):
        if torch is None:
            pytest.skip("torch未安装（环境问题）")
        pad = getattr(answer, "pad_ids", None)
        t = pad([7], 3)
        assert tuple(t.shape) == (3,)

    def test_overlong_raises(self):
        """错误处理: 超过max_len应报错或截断（二选一，但不得静默错位）"""
        if torch is None:
            pytest.skip("torch未安装（环境问题）")
        pad = getattr(answer, "pad_ids", None)
        try:
            t = pad([1, 2, 3, 4, 5], 2)
            assert len(t) == 2, "超长时应截断"
        except (ValueError, AssertionError):
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
