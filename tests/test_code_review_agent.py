"""Code Review Agent 测试套件"""
import os
import sys
import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))


class MockLLMClient:
    """用于测试的模拟LLM客户端"""

    def __init__(self, response_content="", available=True):
        self.response_content = response_content
        self.available = available
        self.call_count = 0
        self.last_messages = None
        self.last_kwargs = None

    def chat(self, messages, model=None, temperature=0.7, max_tokens=2000):
        self.call_count += 1
        self.last_messages = messages
        self.last_kwargs = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if not self.available:
            return None
        response = MagicMock()
        response.content = self.response_content
        return response

    def is_available(self):
        return self.available

    def _extract_json(self, content):
        try:
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass
        return None


class TestCodeReviewAgent(unittest.TestCase):
    """CodeReviewAgent 类测试"""

    def setUp(self):
        from src.agents.code_review_agent import CodeReviewAgent, CodeReviewResult
        self.CodeReviewAgent = CodeReviewAgent
        self.CodeReviewResult = CodeReviewResult
        self.sample_task = {
            "title": "Day1 任务",
            "description": "实现一个简单的计算器",
            "goal": "掌握函数定义"
        }
        self.sample_test_result = {
            "total": 5,
            "passed": 3,
            "failed": 2,
            "errors": 0,
            "details": [
                {"test_name": "test_add", "status": "passed", "message": ""},
                {"test_name": "test_sub", "status": "failed", "message": "AssertionError"},
            ]
        }
        self.sample_code = "def add(a, b):\n    return a + b"

    def test_import_code_review_agent(self):
        from src.agents.code_review_agent import CodeReviewAgent
        self.assertTrue(callable(CodeReviewAgent))

    def test_import_code_review_result(self):
        from src.agents.code_review_agent import CodeReviewResult
        result = CodeReviewResult(
            score=80.0, summary="test", strengths=[], issues=[],
            knowledge_gaps=[], improvement=[], next_learning=[]
        )
        self.assertEqual(result.score, 80.0)

    def test_default_result_when_llm_unavailable(self):
        mock_client = MockLLMClient(available=False)
        agent = self.CodeReviewAgent(mock_client)
        result = agent.review(self.sample_code, self.sample_task, self.sample_test_result)

        self.assertEqual(result.score, 70.0)
        self.assertIn("不可用", result.summary)
        self.assertEqual(result.strengths, [])
        self.assertEqual(result.knowledge_gaps, [])

    def test_successful_review_with_mock_response(self):
        mock_response_json = json.dumps({
            "score": 88,
            "summary": "代码质量良好",
            "strengths": ["命名清晰", "逻辑正确"],
            "issues": ["缺少类型注解"],
            "knowledge_gaps": ["异常处理"],
            "improvement": ["添加文档字符串"],
            "next_learning": ["学习类型提示"]
        })
        mock_client = MockLLMClient(response_content=mock_response_json, available=True)
        agent = self.CodeReviewAgent(mock_client)
        result = agent.review(self.sample_code, self.sample_task, self.sample_test_result)

        self.assertEqual(result.score, 88.0)
        self.assertEqual(result.summary, "代码质量良好")
        self.assertIn("命名清晰", result.strengths)
        self.assertEqual(mock_client.call_count, 1)

    def test_json_parsing_from_llm_response(self):
        mock_response_json = json.dumps({
            "score": 75,
            "summary": "测试总结",
            "strengths": ["优点1"],
            "issues": ["问题1"],
            "knowledge_gaps": ["漏洞1"],
            "improvement": ["改进1"],
            "next_learning": ["下一步1"]
        })
        mock_client = MockLLMClient(response_content=mock_response_json, available=True)
        agent = self.CodeReviewAgent(mock_client)
        result = agent._parse_response(mock_response_json)

        self.assertEqual(result.score, 75.0)
        self.assertEqual(result.summary, "测试总结")
        self.assertEqual(len(result.strengths), 1)
        self.assertEqual(len(result.issues), 1)

    def test_malformed_json_fallback(self):
        mock_client = MockLLMClient(response_content="这不是JSON", available=True)
        agent = self.CodeReviewAgent(mock_client)
        result = agent._parse_response("这不是JSON")

        self.assertEqual(result.score, 70.0)
        self.assertIn("不可用", result.summary)

    def test_malformed_json_with_extra_text(self):
        mock_client = MockLLMClient(available=True)
        agent = self.CodeReviewAgent(mock_client)
        malformed = "前缀文本 {\"score\": 90, \"summary\": \"ok\", \"strengths\": [], \"issues\": [], \"knowledge_gaps\": [], \"improvement\": [], \"next_learning\": []} 后缀文本"
        result = agent._parse_response(malformed)
        self.assertEqual(result.score, 90.0)

    def test_prompt_construction(self):
        mock_client = MockLLMClient(response_content=json.dumps({
            "score": 70, "summary": "", "strengths": [], "issues": [],
            "knowledge_gaps": [], "improvement": [], "next_learning": []
        }), available=True)
        agent = self.CodeReviewAgent(mock_client)

        history = [{"day": 1, "error_type": "syntax", "message": "SyntaxError"}]
        agent.review(self.sample_code, self.sample_task, self.sample_test_result, history)

        self.assertEqual(mock_client.call_count, 1)
        messages = mock_client.last_messages
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")
        self.assertIn("Day1 任务", messages[1]["content"])
        self.assertIn(self.sample_code, messages[1]["content"])
        self.assertIn("历史错误记录", messages[1]["content"])

    def test_result_to_dict(self):
        result = self.CodeReviewResult(
            score=92.0, summary="优秀", strengths=["s1", "s2"],
            issues=["i1"], knowledge_gaps=["g1"], improvement=["imp1"],
            next_learning=["nl1"]
        )
        d = result.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["score"], 92.0)
        self.assertEqual(d["summary"], "优秀")
        self.assertEqual(len(d["strengths"]), 2)
        self.assertEqual(d["issues"], ["i1"])
        self.assertEqual(d["knowledge_gaps"], ["g1"])
        self.assertEqual(d["improvement"], ["imp1"])
        self.assertEqual(d["next_learning"], ["nl1"])

    def test_result_to_dict_default(self):
        result = self.CodeReviewResult(
            score=70.0, summary="s", strengths=[], issues=[],
            knowledge_gaps=[], improvement=[], next_learning=[]
        )
        d = result.to_dict()
        self.assertEqual(d["score"], 70.0)
        self.assertIsInstance(d["strengths"], list)
        self.assertEqual(len(d["strengths"]), 0)

    def test_review_with_failed_tests_detail(self):
        mock_client = MockLLMClient(response_content=json.dumps({
            "score": 60, "summary": "需要改进", "strengths": [],
            "issues": ["测试未通过"], "knowledge_gaps": [],
            "improvement": [], "next_learning": []
        }), available=True)
        agent = self.CodeReviewAgent(mock_client)
        agent.review(self.sample_code, self.sample_task, self.sample_test_result)

        user_msg = mock_client.last_messages[1]["content"]
        self.assertIn("失败/错误详情", user_msg)
        self.assertIn("test_sub", user_msg)

    def test_review_no_history(self):
        mock_client = MockLLMClient(response_content=json.dumps({
            "score": 70, "summary": "", "strengths": [], "issues": [],
            "knowledge_gaps": [], "improvement": [], "next_learning": []
        }), available=True)
        agent = self.CodeReviewAgent(mock_client)
        agent.review(self.sample_code, self.sample_task, self.sample_test_result, history=None)

        user_msg = mock_client.last_messages[1]["content"]
        self.assertNotIn("历史错误记录", user_msg)


class TestDeepSeekClient(unittest.TestCase):
    """DeepSeekClient 类测试"""

    def test_import_deepseek_client(self):
        from src.llm.deepseek_client import DeepSeekClient
        self.assertTrue(callable(DeepSeekClient))

    def test_llm_client_alias(self):
        from src.llm import LLMClient, DeepSeekClient
        self.assertIs(LLMClient, DeepSeekClient)

    def test_llm_init_exports(self):
        from src.llm import BaseLLMClient, LLMResponse, DeepSeekClient, LLMClient
        self.assertTrue(callable(BaseLLMClient))
        self.assertTrue(callable(DeepSeekClient))
        self.assertIs(LLMClient, DeepSeekClient)

    @patch.dict(os.environ, {}, clear=True)
    def test_deepseek_client_availability_without_api_key(self):
        from src.llm.deepseek_client import DeepSeekClient
        client = DeepSeekClient(config_path="nonexistent_config.yaml")
        self.assertFalse(client.is_available())
        self.assertIsNone(client.client)

    def test_deepseek_chat_returns_none_when_unavailable(self):
        from src.llm.deepseek_client import DeepSeekClient
        client = DeepSeekClient(config_path="nonexistent_config.yaml")
        result = client.chat([{"role": "user", "content": "hello"}])
        self.assertIsNone(result)

    def test_config_loading_nonexistent_file(self):
        from src.llm.deepseek_client import DeepSeekClient
        client = DeepSeekClient(config_path="nonexistent_config.yaml")
        self.assertEqual(client.config, {})
        self.assertEqual(client.model, "deepseek-chat")

    def test_config_loading_existing_file(self):
        import tempfile
        import yaml
        from src.llm.deepseek_client import DeepSeekClient

        config = {"deepseek": {"model": "test-model", "base_url": "http://test.com"}}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name

        try:
            client = DeepSeekClient(config_path=config_path)
            self.assertEqual(client.model, "test-model")
        finally:
            os.unlink(config_path)

    def test_extract_json_valid(self):
        from src.llm.deepseek_client import DeepSeekClient
        client = DeepSeekClient.__new__(DeepSeekClient)
        result = client._extract_json('{"key": "value", "num": 42}')
        self.assertEqual(result, {"key": "value", "num": 42})

    def test_extract_json_with_prefix_suffix(self):
        from src.llm.deepseek_client import DeepSeekClient
        client = DeepSeekClient.__new__(DeepSeekClient)
        result = client._extract_json('前缀{"key": "value"}后缀')
        self.assertEqual(result, {"key": "value"})

    def test_extract_json_invalid(self):
        from src.llm.deepseek_client import DeepSeekClient
        client = DeepSeekClient.__new__(DeepSeekClient)
        result = client._extract_json("not json at all")
        self.assertIsNone(result)

    def test_extract_json_nested(self):
        from src.llm.deepseek_client import DeepSeekClient
        client = DeepSeekClient.__new__(DeepSeekClient)
        data = {"outer": {"inner": [1, 2, 3]}}
        result = client._extract_json(json.dumps(data))
        self.assertEqual(result, data)

    def test_extract_json_empty_object(self):
        from src.llm.deepseek_client import DeepSeekClient
        client = DeepSeekClient.__new__(DeepSeekClient)
        result = client._extract_json("{}")
        self.assertEqual(result, {})


class TestBaseLLMClient(unittest.TestCase):
    """BaseLLMClient 抽象基类测试"""

    def test_cannot_instantiate_directly(self):
        from src.llm.base_client import BaseLLMClient
        with self.assertRaises(TypeError):
            BaseLLMClient()

    def _make_client(self):
        """创建用于测试的具体子类实例"""
        from src.llm.base_client import BaseLLMClient
        
        class TestClient(BaseLLMClient):
            def chat(self, messages, model=None, temperature=0.7, max_tokens=2000):
                return None
            def chat_stream(self, messages, model=None, temperature=0.7, max_tokens=2000):
                yield ""
            def is_available(self):
                return False
        
        return TestClient()

    def test_extract_json_valid(self):
        client = self._make_client()
        result = client._extract_json('{"a": 1, "b": "two"}')
        self.assertEqual(result, {"a": 1, "b": "two"})

    def test_extract_json_with_surrounding_text(self):
        client = self._make_client()
        result = client._extract_json('Here is the result: {"score": 85} hope that helps')
        self.assertEqual(result, {"score": 85})

    def test_extract_json_invalid(self):
        client = self._make_client()
        result = client._extract_json("no json here")
        self.assertIsNone(result)

    def test_extract_json_empty_string(self):
        client = self._make_client()
        result = client._extract_json("")
        self.assertIsNone(result)

    def test_extract_json_multiple_braces(self):
        client = self._make_client()
        result = client._extract_json('{"a": {"b": 2}}')
        self.assertEqual(result, {"a": {"b": 2}})

    def test_llm_response_dataclass(self):
        from src.llm.base_client import LLMResponse
        resp = LLMResponse(
            content="hello", model="m1",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop"
        )
        self.assertEqual(resp.content, "hello")
        self.assertEqual(resp.model, "m1")
        self.assertEqual(resp.usage["total_tokens"], 30)
        self.assertEqual(resp.finish_reason, "stop")


if __name__ == "__main__":
    unittest.main()
