# Day 34 Tests: Agent架构
#
# answer.py 必须实现（接口约定）:
# - Tool(name, func, description)          数据类/类
# - Agent(tools)  .run(goal) -> list[dict] 轨迹；按description关键词匹配工具执行；
#   无匹配时轨迹含 {"action": "clarify"}
# - Memory()  .append(item) / .recall(n) -> 最近n条（时间升序）
# - plan_step(goal, tools) -> dict  关键词匹配选择{"tool","reason"}; 无匹配tool="clarify"
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


def _tools():
    Tool = _require("Tool")
    return [
        Tool(name="search", func=lambda q: f"结果:{q}", description="搜索 网络查询资料"),
        Tool(name="calc", func=lambda x: x * 2, description="计算 数学运算"),
    ]


@pytest.mark.skill("agent.tool", "agent.memory")
class TestTool:
    def test_tool_fields(self):
        Tool = _require("Tool")
        t = Tool(name="t", func=lambda x: x, description="测试 工具")
        assert t.name == "t" and callable(t.func)

    def test_tool_executes(self):
        tools = _tools()
        assert tools[1].func(21) == 42


@pytest.mark.skill("agent.tool", "agent.memory")
class TestAgent:
    def test_picks_correct_tool(self):
        """基础功能: 按关键词路由到正确工具"""
        agent_cls = _require("Agent")
        trace = agent_cls(_tools()).run("帮我搜索 python教程")
        assert any("搜索" in str(step) or "search" in str(step) for step in trace), \
            f"应调用search工具: {trace}"

    def test_unknown_goal_clarify(self):
        """错误处理: 无匹配工具→clarify而非崩溃"""
        agent_cls = _require("Agent")
        trace = agent_cls(_tools()).run("完全无关的任务xyz")
        assert isinstance(trace, (list, dict))
        text = str(trace)
        assert "clarify" in text.lower() or "澄清" in text

    def test_run_terminates(self):
        """决策循环必须终止"""
        agent_cls = _require("Agent")
        trace = agent_cls(_tools()).run("搜索 资料")
        steps = trace if isinstance(trace, list) else trace.get("steps", [])
        assert len(steps) <= 10, f"循环未终止: {len(steps)}步"


@pytest.mark.skill("agent.tool", "agent.memory")
class TestMemory:
    def test_recall_last_n_in_order(self):
        if answer is None:
            pytest.skip("no answer.py under review")
        mem_cls = getattr(answer, "Memory", None)
        if mem_cls is None:
            pytest.fail("必须实现 Memory 类")
        m = mem_cls()
        for i in range(5):
            m.append(i)
        recalled = list(m.recall(3))
        assert recalled == [2, 3, 4], f"recall(n)应为最近n条且保持时间升序: {recalled}"

    def test_recall_empty(self):
        if answer is None:
            pytest.skip("no answer.py under review")
        mem_cls = getattr(answer, "Memory", None)
        assert list(mem_cls().recall(3)) == []


@pytest.mark.skill("agent.tool", "agent.tool_calling")
class TestPlanner:
    """Tool→Planner→Execution→Memory 中的 Planner 环节"""

    def _tools(self):
        Tool = _require("Tool")
        return [
            Tool(name="weather", func=lambda city: f"晴 {city}", description="查询城市天气"),
            Tool(name="search", func=lambda q: f"结果:{q}", description="网页搜索资料"),
        ]

    def test_picks_matching_tool(self):
        plan = _require("plan_step")
        decision = plan("查一下北京weather怎么样", self._tools())
        assert isinstance(decision, dict)
        assert decision.get("tool") == "weather", f"应选择weather工具: {decision}"
        assert isinstance(decision.get("reason"), str) and decision["reason"].strip()

    def test_unrelated_goal_clarify(self):
        plan = _require("plan_step")
        decision = plan("帮我写一首诗", self._tools())
        assert decision.get("tool") == "clarify", f"无匹配工具应请求澄清: {decision}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
