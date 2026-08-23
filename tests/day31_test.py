# Day 31 Tests: LLM客户端
#
# answer.py 必须实现（接口约定）:
# - LLMError(Exception)
# - LLMClient(api_key=None)  .is_available() -> bool；api_key为None时不可用
#                            .chat(messages) 在不可用时抛 LLMError
# - parse_response(text) -> dict    从LLM文本中提取JSON（容忍前后缀文本）
# - chunk_text(text, max_chars) -> list[str]   按max_chars切块；max_chars<1抛ValueError
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
    obj = getattr(answer, name, None)
    if obj is None:
        pytest.fail(f"必须实现 {name}")
    return obj


class TestAvailability:
    def test_no_key_not_available(self):
        client_cls = _require("LLMClient")
        assert not client_cls().is_available(), "无api_key时is_available应为False"

    def test_with_key_available(self):
        client_cls = _require("LLMClient")
        assert client_cls(api_key="sk-test").is_available()

    def test_chat_without_key_raises(self):
        """错误处理: 未配置key时chat必须抛LLMError"""
        if answer is None:
            pytest.skip("no answer.py under review")
        err_cls = getattr(answer, "LLMError", None)
        if err_cls is None:
            pytest.fail("必须实现 LLMError")
        client_cls = _require("LLMClient")
        with pytest.raises(err_cls):
            client_cls().chat([{"role": "user", "content": "hi"}])

    def test_llm_error_hierarchy(self):
        err_cls = _require("LLMError")
        assert issubclass(err_cls, Exception)


class TestParseResponse:
    def test_plain_json(self):
        parse = _require("parse_response")
        out = parse('{"score": 85}')
        assert isinstance(out, dict) and out["score"] == 85

    def test_json_with_surrounding_text(self):
        """边界条件: LLM常输出```json ... ```包裹"""
        parse = _require("parse_response")
        text = '好的，结果如下：\n```json\n{"summary": "ok", "items": [1,2]}\n```\n完毕'
        out = parse(text)
        assert out.get("summary") == "ok" and out["items"] == [1, 2]

    def test_invalid_returns_none_or_raises(self):
        parse = _require("parse_response")
        try:
            out = parse("完全没有JSON的内容")
            assert out is None
        except (ValueError, TypeError):
            pass


class TestChunking:
    def test_chunk_sizes(self):
        chunk = _require("chunk_text")
        parts = chunk("abcdefghij", 4)
        assert "".join(parts) == "abcdefghij"
        assert all(len(p) <= 4 for p in parts)

    def test_invalid_max_chars(self):
        """错误处理"""
        chunk = _require("chunk_text")
        with pytest.raises(ValueError):
            chunk("abc", 0)

    def test_empty_text(self):
        chunk = _require("chunk_text")
        assert list(chunk("", 5)) == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
