# Day 24 Tests: Transformer核心组件 (PyTorch)
#
# answer.py 必须实现（接口约定）:
# - scaled_dot_product_attention(q, k, v) -> (output, attn_weights)
#   softmax(QK^T/sqrt(d_k))V；attn每行和为1
# - MultiHeadSelfAttention(d_model, num_heads) -> nn.Module
# - PositionalEncoding(max_len, d_model) -> nn.Module  标准sin/cos编码，含buffer
import math

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
    obj = getattr(answer, name, None)
    if obj is None:
        pytest.fail(f"必须实现 {name}")
    return obj


@requires_torch
@pytest.mark.skill("transformer.attention", "transformer.positional_encoding")
class TestAttention:
    def test_output_shape_and_weights_sum(self):
        attn_fn = _require("scaled_dot_product_attention")
        q = torch.randn(1, 4, 8)  # (B, T, d)
        k = torch.randn(1, 4, 8)
        v = torch.randn(1, 4, 8)
        out, weights = attn_fn(q, k, v)
        assert tuple(out.shape) == tuple(v.shape), f"输出shape应与v一致"
        assert torch.allclose(weights.sum(dim=-1), torch.ones(1, 4), atol=1e-5), "注意力权重每行和必须为1"

    def test_attention_focuses_on_matching(self):
        """边界条件: q与某个k完全匹配时该位置权重最大"""
        attn_fn = _require("scaled_dot_product_attention")
        k = torch.randn(1, 3, 4)
        q = k[:, 2:3, :]  # 与第2个key相同
        _, w = attn_fn(q, k, k)
        assert float(w[0, 0].argmax()) == 2

    def test_scaling_prevents_saturation(self):
        """大维度下除以sqrt(d_k)：权重不应全部接近one-hot"""
        attn_fn = _require("scaled_dot_product_attention")
        d = 64
        q = torch.randn(1, 5, d) * math.sqrt(d)
        _, w = attn_fn(q, torch.randn(1, 5, d), torch.randn(1, 5, d))
        assert w.max() < 0.999, "未做scale时权重会饱和到one-hot"


@requires_torch
@pytest.mark.skill("transformer.attention", "transformer.positional_encoding")
class TestMultiHead:
    def test_forward_shape(self):
        mha_cls = _require("MultiHeadSelfAttention")
        mha = mha_cls(d_model=32, num_heads=4)
        x = torch.randn(2, 6, 32)  # (B, T, d_model)
        out = mha(x)
        assert tuple(out.shape) == (2, 6, 32)

    def test_invalid_head_split_raises(self):
        """错误处理: d_model不能被heads整除"""
        mha_cls = _require("MultiHeadSelfAttention")
        with pytest.raises((ValueError, AssertionError)):
            mha_cls(d_model=30, num_heads=4)


@requires_torch
@pytest.mark.skill("transformer.attention", "transformer.positional_encoding")
class TestPositionalEncoding:
    def test_known_values_at_pos_zero(self):
        """标准公式: pe[0, 2i]=sin(0)=0, pe[0, 2i+1]=cos(0)=1"""
        pe_cls = _require("PositionalEncoding")
        pe_mod = pe_cls(max_len=16, d_model=8)
        buf_name = next((n for n, b in pe_mod.named_buffers() if b.shape[0] >= 16), None)
        assert buf_name is not None, "PositionalEncoding应包含position buffer"
        table = dict(pe_mod.named_buffers())[buf_name]
        assert abs(float(table[0, 0])) < 1e-6, "pe[0,0]应为sin(0)=0"
        assert abs(float(table[0, 1]) - 1.0) < 1e-6, "pe[0,1]应为cos(0)=1"

    def test_values_bounded(self):
        """边界条件: 所有值在[-1,1]"""
        pe_cls = _require("PositionalEncoding")
        table = list(pe_cls(32, 16).buffers())[0]
        assert table.abs().max() <= 1.0 + 1e-6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
