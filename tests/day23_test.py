# Day 23 Tests: NLP基础 (PyTorch)
#
# answer.py 必须实现（接口约定）:
# - tokenize(text) -> list[str]           小写化、去标点、按空格分词
# - build_vocab(texts, min_freq=1) -> dict  {"<pad>":0, "<unk>":1, 词: idx...}
# - text_to_ids(text, vocab, max_len) -> list[int]  编码+padding/truncate到max_len
# - TextClassifier(vocab_size, embed_dim=16, num_classes=2)  mean-pool embedding + linear
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


@pytest.mark.skill("nlp.tokenization", "nlp.embedding")
class TestTokenize:
    def test_lowercase_and_split(self):
        tok = _require("tokenize")
        assert tok("Hello World") == ["hello", "world"]

    def test_punctuation_removed(self):
        """任务要求检查: 标点应被去除"""
        tok = _require("tokenize")
        out = tok("I like ML, and PyTorch!")
        assert all(t.isalpha() for t in out), f"标点未清除: {out}"
        assert "ml" in out and "pytorch" in out

    def test_empty_string(self):
        """边界条件"""
        tok = _require("tokenize")
        assert tok("") == []


@pytest.mark.skill("nlp.tokenization", "nlp.embedding")
class TestVocab:
    def test_special_tokens(self):
        build = _require("build_vocab")
        vocab = build(["a b", "b c"])
        assert vocab.get("<pad>") == 0 and vocab.get("<unk>") == 1

    def test_word_indices(self):
        build = _require("build_vocab")
        vocab = build(["apple banana", "banana"])
        assert vocab["banana"] > 0
        assert "apple" in vocab and "c" not in vocab

    def test_min_freq_filter(self):
        """边界条件: min_freq过滤低频词"""
        build = _require("build_vocab")
        vocab = build(["a b a", "c"], min_freq=2)
        assert "a" in vocab
        assert "b" not in vocab and "c" not in vocab


@pytest.mark.skill("nlp.tokenization", "nlp.embedding")
class TestEncoding:
    def test_ids_and_padding(self):
        enc = _require("text_to_ids")
        build = _require("build_vocab")
        vocab = build(["hello world"])
        ids = enc("hello world", vocab, max_len=5)
        assert len(ids) == 5
        assert ids[-1] == 0, "padding应为<pad>=0"

    def test_truncation(self):
        enc = _require("text_to_ids")
        build = _require("build_vocab")
        vocab = build(["a b c d e f"])
        ids = enc("a b c d e f", vocab, max_len=3)
        assert len(ids) == 3, "超长必须截断到max_len"

    def test_unknown_word_maps_unk(self):
        enc = _require("text_to_ids")
        build = _require("build_vocab")
        vocab = build(["known words"])
        ids = enc("unknownword", vocab, max_len=2)
        assert ids[0] == 1, "OOV词必须映射为<unk>=1"


@requires_torch
@pytest.mark.skill("nlp.tokenization", "nlp.embedding")
class TestClassifier:
    def test_forward_shape(self):
        if answer is None:
            pytest.skip("no answer.py under review")
        cls = getattr(answer, "TextClassifier", None)
        if cls is None:
            pytest.fail("必须实现 TextClassifier 类")
        model = cls(vocab_size=100)
        x = torch.randint(0, 100, (4, 7))
        out = model(x)
        assert tuple(out.shape) == (4, 2), f"输出shape错误: {tuple(out.shape)}"

    def test_backward(self):
        if answer is None:
            pytest.skip("no answer.py under review")
        cls = getattr(answer, "TextClassifier", None)
        if cls is None:
            pytest.fail("必须实现 TextClassifier 类")
        model = cls(50, embed_dim=8, num_classes=3)
        loss = nn.CrossEntropyLoss()(model(torch.randint(0, 50, (2, 5))),
                                     torch.tensor([0, 1]))
        loss.backward()
        grads = [p.grad for p in model.parameters() if p.grad is not None]
        assert len(grads) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
