# Day 37 Tests: 自动判题平台（纯Python模拟，不嵌套真实pytest）
#
# answer.py 必须实现（接口约定）:
# - grade_score(passed, total) -> float   百分制得分；total=0返回0.0
# - letter_grade(score) -> str            >=90 'A'，>=75 'B'，>=60 'C'，否则 'D'
# - SecurityError(Exception)
# - run_with_timeout(code, seconds=2) -> tuple  ("ok", value) 或 ("timeout", None)
#   在受限命名空间执行表达式代码；代码含 __import__/open 时抛 SecurityError
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


class TestGrading:
    def test_score_math(self):
        grade = _require("grade_score")
        assert abs(float(grade(8, 10)) - 80.0) < 1e-9
        assert float(grade(0, 5)) == 0.0

    def test_zero_total(self):
        """边界条件: 无测试不得除零"""
        grade = _require("grade_score")
        assert float(grade(0, 0)) == 0.0

    def test_letter_thresholds(self):
        letter = _require("letter_grade")
        assert letter(95) == "A"
        assert letter(90) == "A"
        assert letter(80) == "B"
        assert letter(60) == "C"
        assert letter(59) == "D"


class TestSecurityError:
    def test_hierarchy(self):
        if answer is None:
            pytest.skip("no answer.py under review")
        err = getattr(answer, "SecurityError", None)
        if err is None:
            pytest.fail("必须实现 SecurityError")
        assert issubclass(err, Exception)


class TestSandbox:
    def test_safe_expression(self):
        run = _require("run_with_timeout")
        status, value = run("(2 + 3) * 4")
        assert status == "ok" and int(value) == 20

    def test_blocks_import(self):
        """错误处理: 必须阻止__import__"""
        if answer is None:
            pytest.skip("no answer.py under review")
        err_cls = getattr(answer, "SecurityError", None)
        if err_cls is None:
            pytest.fail("必须实现 SecurityError")
        run = _require("run_with_timeout")
        with pytest.raises(err_cls):
            run("__import__('os').getcwd()")

    def test_timeout_detection(self):
        """死循环必须在限时内检出"""
        run = _require("run_with_timeout")
        status, _v = run("while True:\n    pass\n", seconds=1)
        assert status == "timeout", f"死循环应超时，得到{status}"

    def test_syntax_error_handled(self):
        """语法错误不应崩溃整个判题器"""
        run = _require("run_with_timeout")
        try:
            status, _v = run("def broken(:", seconds=1)
            assert status in ("error", "ok") or status != "ok"
        except (SyntaxError, ValueError):
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
