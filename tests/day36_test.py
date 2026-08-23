# Day 36 Tests: Code Agent
#
# answer.py 必须实现（接口约定）:
# - generate_function_source(name, args, return_expr) -> str
#   生成可编译的函数定义代码，如 ("add", "a, b", "a + b") → "def add(a, b):\n    return a + b"
# - review_code(code) -> list[str]  检出问题：使用eval(、裸except等，无问题时返回空列表
# - has_missing_colon(line) -> bool 检测缺冒号的def/if/for/while行
# - rename_variable(code, old, new) -> str  词边界安全重命名
import ast

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


class TestCodeGeneration:
    def test_generated_code_compiles(self):
        gen = _require("generate_function_source")
        src = gen("add", "a, b", "a + b")
        tree = ast.parse(src)  # 编译失败会抛SyntaxError
        assert any(isinstance(n, ast.FunctionDef) and n.name == "add" for n in ast.walk(tree))

    def test_generated_code_runs(self):
        """基础功能: 生成的代码可执行且行为正确"""
        gen = _require("generate_function_source")
        src = gen("mul2", "x", "x * 2")
        ns = {}
        exec(src, ns)
        assert ns["mul2"](21) == 42

    def test_invalid_name_raises(self):
        """错误处理: 非法函数名"""
        gen = _require("generate_function_source")
        with pytest.raises((ValueError, SyntaxError)):
            gen("1bad-name", "x", "x")


class TestReview:
    def test_flags_eval_usage(self):
        review = _require("review_code")
        issues = review("result = eval(input())")
        assert len(issues) >= 1, "必须检出eval(的使用"

    def test_clean_code_no_issues(self):
        """边界条件: 干净代码零告警"""
        review = _require("review_code")
        issues = review("def add(a, b):\n    return a + b\n")
        assert list(issues) == []

    def test_bare_except_flagged(self):
        review = _require("review_code")
        issues = review("try:\n    x = 1\nexcept:\n    pass")
        assert any("except" in i.lower() for i in issues), "应检出裸except"


class TestMissingColon:
    def test_detects_missing_colon(self):
        detect = _require("has_missing_colon")
        assert detect("def foo()") is True
        assert detect("if x > 1") is True

    def test_valid_lines_pass(self):
        detect = _require("has_missing_colon")
        assert detect("def foo():") is False
        assert detect("return a + b") is False


class TestRenameVariable:
    def test_word_boundary_rename(self):
        rename = _require("rename_variable")
        code = "total = 1\ndef f(total_value):\n    return total + total_value"
        out = rename(code, "total", "sum_all")
        # total_value 不能被误改成 sum_all_value 的部分错乱——词边界检查
        assert "total_value" in out or "sum_all_value" not in out.replace("total_value", "")
        assert "sum_all =" in out and "sum_all +" in out

    def test_no_partial_match(self):
        """边界条件: 子串不能被误替换"""
        rename = _require("rename_variable")
        out = rename("data_count = data", "data", "dataset")
        assert "dataset_count" not in out.split("=")[0], "词边界错误: data_count被误改"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
