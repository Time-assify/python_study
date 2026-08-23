# Day 32 Tests: Prompt Engineering
#
# answer.py 必须实现（接口约定）:
# - build_few_shot_prompt(examples, query) -> str
#   examples为[(question, answer), ...]；query必须出现在examples之后
# - chain_of_thought(question) -> str   包含"一步步"/"step by step"引导语与问题本身
# - system_prompt(role, instructions) -> str  以role开头并包含instructions
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


@pytest.mark.skill("prompt.few_shot", "prompt.chain_of_thought")
class TestFewShot:
    def test_contains_examples_and_query(self):
        build = _require("build_few_shot_prompt")
        text = build([("2+2=?", "4"), ("3+3=?", "6")], "5+5=?")
        for frag in ("2+2=?", "4", "3+3=?", "6", "5+5=?"):
            assert frag in text, f"prompt缺少内容: {frag}"

    def test_query_after_examples(self):
        """任务要求检查: few-shot顺序——示例在前，查询在后"""
        build = _require("build_few_shot_prompt")
        text = build([("Q1", "A1")], "QUERY")
        assert text.index("A1") < text.index("QUERY"), "query必须位于示例之后"

    def test_empty_examples(self):
        """边界条件: 无示例也能构建"""
        build = _require("build_few_shot_prompt")
        assert "hello" in build([], "hello")

    def test_non_list_raises(self):
        """错误处理"""
        build = _require("build_few_shot_prompt")
        with pytest.raises((TypeError, ValueError)):
            build("not-a-list", "q")


@pytest.mark.skill("prompt.few_shot", "prompt.chain_of_thought")
class TestChainOfThought:
    def test_contains_guidance(self):
        cot = _require("chain_of_thought")
        text = cot("9.11和9.8哪个大？")
        low = text.lower()
        assert ("一步步" in text) or ("step" in low), "缺少CoT引导语"
        assert "9.11" in text, "应包含原问题"


@pytest.mark.skill("prompt.few_shot", "prompt.chain_of_thought")
class TestSystemPrompt:
    def test_role_first(self):
        sys_fn = _require("system_prompt")
        text = sys_fn("资深Python导师", "引导学生思考")
        assert text.strip().startswith("资深Python导师"), "system prompt应以role开头"
        assert "引导学生思考" in text

    def test_nonempty_instructions(self):
        sys_fn = _require("system_prompt")
        with pytest.raises((ValueError, TypeError)):
            sys_fn("role", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
