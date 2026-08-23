# Day 35 Tests: Tool Calling
#
# answer.py 必须实现（接口约定）:
# - ToolError(Exception)
# - tool_schema(name, params) -> dict
#   params为 {参数名: 类型字符串} 如 {"n": "int"}；输出含 name/parameters/required 的JSON-schema风格dict
# - execute_tool(schema, args) -> 调用结果   严格类型校验：bool不是int、str不是number；不匹配抛ToolError
# - append_result(history, result) -> list   追加并返回新历史
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


def _schema():
    build = _require("tool_schema")
    return build("add", {"a": "int", "b": "int"})


@pytest.mark.skill("agent.schema_validation", "agent.tool_calling")
class TestSchema:
    def test_schema_structure(self):
        schema = _schema()
        text = str(schema)
        assert "add" in text and ("a" in text and "b" in text), f"schema缺少工具信息: {schema}"
        assert isinstance(schema, dict)

    def test_required_params_listed(self):
        schema = _schema()
        required = schema.get("required", [])
        assert set(required) >= {"a", "b"}, f"required应包含全部参数: {schema}"


@pytest.mark.skill("agent.schema_validation", "agent.tool_calling")
class TestExecuteTool:
    def test_valid_call(self):
        execute = _require("execute_tool")
        schema = _schema()
        schema["_func"] = lambda a, b: a + b  # 允许测试注入实现
        result = execute(schema, {"a": 2, "b": 3})
        try:
            assert result == 5
        except AssertionError:
            # 也可能返回{"result":5}形式
            assert result.get("result") == 5

    def test_bool_is_not_int(self):
        """严格类型: Python中bool是int子类，但tool调用必须拒绝"""
        if answer is None:
            pytest.skip("no answer.py under review")
        err_cls = getattr(answer, "ToolError", None)
        if err_cls is None:
            pytest.fail("必须实现 ToolError")
        execute = _require("execute_tool")
        schema = _schema()
        schema["_func"] = lambda a, b: a + b
        with pytest.raises(err_cls):
            execute(schema, {"a": True, "b": 1})

    def test_wrong_type_raises(self):
        """错误处理: str传入int参数"""
        if answer is None:
            pytest.skip("no answer.py under review")
        err_cls = getattr(answer, "ToolError", None)
        if err_cls is None:
            pytest.fail("必须实现 ToolError")
        execute = _require("execute_tool")
        schema = _schema()
        schema["_func"] = lambda a, b: a + b
        with pytest.raises(err_cls):
            execute(schema, {"a": "2", "b": 1})


@pytest.mark.skill("agent.schema_validation", "agent.tool_calling")
class TestHistory:
    def test_append_result(self):
        append = _require("append_result")
        history = [{"step": 0}]
        out = append(history, {"step": 1})
        assert len(out) == 2
        assert out[-1]["step"] == 1
        assert history != out or history == [{"step": 0}], "不应原地破坏旧历史"

    def test_append_preserves_order(self):
        append = _require("append_result")
        h = []
        for i in range(3):
            h = append(h, i)
        assert list(h) == [0, 1, 2]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
