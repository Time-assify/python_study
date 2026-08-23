# Day 31 Tests: LLM客户端
#
# answer.py 必须实现（接口约定）:
# - LLMError(Exception)
# - LLMClient(api_key=None, transport=None)
#     .is_available() -> bool        api_key为None时不可用
#     .chat(messages)                不可用时抛 LLMError
#     .chat_stream(messages)         生成器：逐段yield字符串chunk；
#                                    未配置api_key抛LLMError；无transport抛LLMError；
#                                    有transport时从transport(messages)逐块读取
# - parse_response(text) -> dict     从LLM文本中提取JSON（容忍前后缀文本）
# - chunk_text(text, max_chars) -> list[str]   按max_chars切块；max_chars<1抛ValueError
# - retry_call(fn, retries=2, exceptions=(Exception,))
#     调用fn直到成功；最多额外重试retries次；仍失败则抛出最后一次异常
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


@pytest.mark.skill("llm.client", "json_parsing")
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


class FakeTransport:
    """Mock传输层：返回固定chunk序列，禁止真实网络访问"""

    def __init__(self, chunks):
        self.chunks = chunks
        self.call_count = 0

    def __call__(self, messages):
        self.call_count += 1
        return iter(self.chunks)


@pytest.mark.skill("llm.client", "json_parsing")
class TestStreaming:
    """任务要求: 流式响应（全部使用mock，不访问真实API）"""

    def test_stream_yields_chunks_in_order(self):
        stream_fn = getattr(answer, "chat_stream", None)
        client_cls = _require("LLMClient")
        transport = FakeTransport(["chunk1", "chunk2", "chunk3"])
        client = client_cls(api_key="sk-test", transport=transport)

        if stream_fn is not None and not hasattr(client, "chat_stream"):
            gen = stream_fn(client, [{"role": "user", "content": "hi"}])
        else:
            if not callable(getattr(client, "chat_stream", None)):
                pytest.fail("LLMClient必须实现 chat_stream() 方法")
            gen = client.chat_stream([{"role": "user", "content": "hi"}])

        chunks = list(gen)
        assert chunks == ["chunk1", "chunk2", "chunk3"], (
            f"流式输出应按顺序yield全部chunk: {chunks}"
        )

    def test_stream_without_key_raises(self):
        """错误处理: 无key时流式也必须抛LLMError"""
        if answer is None:
            pytest.skip("no answer.py under review")
        err_cls = getattr(answer, "LLMError", None)
        if err_cls is None:
            pytest.fail("必须实现 LLMError")
        client_cls = _require("LLMClient")
        client = client_cls(api_key=None,
                            transport=FakeTransport(["x"]))
        stream = getattr(client, "chat_stream", None)
        if stream is None and callable(getattr(answer, "chat_stream", None)):
            stream = lambda msgs: answer.chat_stream(client, msgs)  # noqa: E731
        if stream is None:
            pytest.fail("LLMClient必须实现 chat_stream()")
        with pytest.raises(err_cls):
            list(stream([{"role": "user", "content": "hi"}]))

    def test_stream_consumes_transport_once_per_call(self):
        client_cls = _require("LLMClient")
        transport = FakeTransport(["a", "b"])
        client = client_cls(api_key="k", transport=transport)
        list(client.chat_stream([{"role": "user", "content": "?"}]))
        assert transport.call_count == 1


@pytest.mark.skill("llm.client", "json_parsing")
class TestRetry:
    """任务要求: 错误重试（全部使用mock）"""

    def test_retry_succeeds_after_transient_errors(self):
        retry_call = _require("retry_call")
        calls = {"n": 0}

        def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise TimeoutError("transient")
            return "ok"

        result = retry_call(flaky, retries=2, exceptions=(TimeoutError,))
        assert result == "ok"
        assert calls["n"] == 3, (
            f"前两次失败第三次成功 → 应恰好调用3次，实际{calls['n']}"
        )

    def test_retry_exhaustion_raises_last_error(self):
        """错误处理: 重试耗尽后抛出最后一次异常"""
        retry_call = _require("retry_call")
        calls = {"n": 0}

        def always_fail():
            calls["n"] += 1
            raise ValueError("boom")

        with pytest.raises(ValueError):
            retry_call(always_fail, retries=2)
        # 首次 + retries次重试
        assert calls["n"] == 3, (
            f"retries=2时应调用首次+2=3次，实际{calls['n']}"
        )


@pytest.mark.skill("llm.client", "json_parsing")
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


@pytest.mark.skill("llm.client", "json_parsing")
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
