"""Code Review Agent 测试套件"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))


class MockLLMClient:
    """用于测试的模拟LLM客户端"""

    def __init__(self, response_content="", available=True, exception=None):
        self.response_content = response_content
        self.available = available
        self.exception = exception
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
        if self.exception:
            raise self.exception
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
        self.sample_day = 1
        self.sample_task = {
            "title": "Day1 任务",
            "description": "实现一个简单的计算器",
            "goal": "掌握函数定义"
        }
        self.sample_requirement = "实现加减乘除四则运算函数"
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
        result = agent.review(self.sample_day, self.sample_code, self.sample_task,
                              self.sample_requirement, self.sample_test_result)

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
        result = agent.review(self.sample_day, self.sample_code, self.sample_task,
                              self.sample_requirement, self.sample_test_result)

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
        agent.review(self.sample_day, self.sample_code, self.sample_task,
                     self.sample_requirement, self.sample_test_result, history)

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
        agent.review(self.sample_day, self.sample_code, self.sample_task,
                     self.sample_requirement, self.sample_test_result)

        user_msg = mock_client.last_messages[1]["content"]
        self.assertIn("失败/错误详情", user_msg)
        self.assertIn("test_sub", user_msg)

    def test_review_no_history(self):
        mock_client = MockLLMClient(response_content=json.dumps({
            "score": 70, "summary": "", "strengths": [], "issues": [],
            "knowledge_gaps": [], "improvement": [], "next_learning": []
        }), available=True)
        agent = self.CodeReviewAgent(mock_client)
        agent.review(self.sample_day, self.sample_code, self.sample_task,
                     self.sample_requirement, self.sample_test_result, history=None)

        user_msg = mock_client.last_messages[1]["content"]
        self.assertNotIn("历史错误记录", user_msg)

    # --- New tests ---

    def test_review_with_day_and_requirement(self):
        mock_client = MockLLMClient(response_content=json.dumps({
            "score": 70, "summary": "", "strengths": [], "issues": [],
            "knowledge_gaps": [], "improvement": [], "next_learning": []
        }), available=True)
        agent = self.CodeReviewAgent(mock_client)
        agent.review(5, self.sample_code, self.sample_task,
                     "自定义要求内容", self.sample_test_result)

        user_msg = mock_client.last_messages[1]["content"]
        self.assertIn("第5天", user_msg)
        self.assertIn("自定义要求内容", user_msg)

    def test_review_exception_fallback(self):
        mock_client = MockLLMClient(available=True, exception=RuntimeError("LLM crashed"))
        agent = self.CodeReviewAgent(mock_client)
        result = agent.review(self.sample_day, self.sample_code, self.sample_task,
                              self.sample_requirement, self.sample_test_result)

        self.assertEqual(result.score, 70.0)
        self.assertEqual(result.review_status, "error")
        self.assertIn("不可用", result.summary)

    def test_review_success_status(self):
        mock_client = MockLLMClient(response_content=json.dumps({
            "score": 85, "summary": "good", "strengths": [], "issues": [],
            "knowledge_gaps": [], "improvement": [], "next_learning": []
        }), available=True)
        agent = self.CodeReviewAgent(mock_client)
        result = agent.review(self.sample_day, self.sample_code, self.sample_task,
                              self.sample_requirement, self.sample_test_result)

        self.assertEqual(result.review_status, "success")

    def test_review_fallback_status(self):
        mock_client = MockLLMClient(available=False)
        agent = self.CodeReviewAgent(mock_client)
        result = agent.review(self.sample_day, self.sample_code, self.sample_task,
                              self.sample_requirement, self.sample_test_result)

        self.assertEqual(result.review_status, "fallback")

    def test_prompt_includes_requirement(self):
        mock_client = MockLLMClient(response_content=json.dumps({
            "score": 70, "summary": "", "strengths": [], "issues": [],
            "knowledge_gaps": [], "improvement": [], "next_learning": []
        }), available=True)
        agent = self.CodeReviewAgent(mock_client)
        agent.review(self.sample_day, self.sample_code, self.sample_task,
                     "必须使用类继承实现", self.sample_test_result)

        user_msg = mock_client.last_messages[1]["content"]
        self.assertIn("必须使用类继承实现", user_msg)

    def test_prompt_includes_day_number(self):
        mock_client = MockLLMClient(response_content=json.dumps({
            "score": 70, "summary": "", "strengths": [], "issues": [],
            "knowledge_gaps": [], "improvement": [], "next_learning": []
        }), available=True)
        agent = self.CodeReviewAgent(mock_client)
        agent.review(3, self.sample_code, self.sample_task,
                     self.sample_requirement, self.sample_test_result)

        user_msg = mock_client.last_messages[1]["content"]
        self.assertIn("第3天", user_msg)


class TestCodeReviewScoring(unittest.TestCase):
    """评分逻辑测试"""

    def _calculate_final_score(self, syntax_valid, execution_success, timeout,
                               test_score, ai_score, ai_available):
        if not syntax_valid or not execution_success or timeout:
            return 0.0
        if test_score < 60:
            return test_score
        if ai_available and ai_score is not None:
            return round(test_score * 0.7 + ai_score * 0.3, 1)
        return test_score

    def test_ai_score_does_not_override_pytest_failure(self):
        score = self._calculate_final_score(
            syntax_valid=True, execution_success=True, timeout=False,
            test_score=40, ai_score=90, ai_available=True
        )
        self.assertEqual(score, 40.0)

    def test_ai_score_used_when_pytest_passes(self):
        score = self._calculate_final_score(
            syntax_valid=True, execution_success=True, timeout=False,
            test_score=80, ai_score=90, ai_available=True
        )
        expected = round(80 * 0.7 + 90 * 0.3, 1)
        self.assertEqual(score, expected)

    def test_syntax_error_gives_zero(self):
        score = self._calculate_final_score(
            syntax_valid=False, execution_success=True, timeout=False,
            test_score=80, ai_score=90, ai_available=True
        )
        self.assertEqual(score, 0.0)

    def test_timeout_gives_zero(self):
        score = self._calculate_final_score(
            syntax_valid=True, execution_success=True, timeout=True,
            test_score=80, ai_score=90, ai_available=True
        )
        self.assertEqual(score, 0.0)


class TestReviewHistory(unittest.TestCase):
    """Review History 数据库操作测试"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_review_history(self):
        from src.database.db import Database
        db = Database(db_path=self.db_path)
        review_result = {"score": 85, "summary": "good"}
        row_id = db.save_review_history(day=1, code_snippet="def foo(): pass",
                                        review_result=review_result)
        self.assertGreater(row_id, 0)
        db.close()

    def test_get_review_history(self):
        from src.database.db import Database
        db = Database(db_path=self.db_path)
        review_result = {"score": 90, "summary": "excellent"}
        db.save_review_history(day=2, code_snippet="x = 1", review_result=review_result)

        history = db.get_review_history(day=2)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["day"], 2)
        self.assertEqual(history[0]["review_result"]["score"], 90)
        self.assertEqual(history[0]["code_snippet"], "x = 1")
        db.close()


class TestDatabaseReviewHistory(unittest.TestCase):
    """数据库 review_history 表创建和CRUD测试"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_review.db")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_review_history_table_creation(self):
        from src.database.db import Database
        db = Database(db_path=self.db_path)
        cursor = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='review_history'"
        )
        table = cursor.fetchone()
        self.assertIsNotNone(table)
        db.close()

    def test_save_and_retrieve_history(self):
        from src.database.db import Database
        db = Database(db_path=self.db_path)
        result1 = {"score": 75, "summary": "needs improvement"}
        result2 = {"score": 92, "summary": "great work"}
        db.save_review_history(day=1, code_snippet="code_a", review_result=result1)
        db.save_review_history(day=1, code_snippet="code_b", review_result=result2)

        all_history = db.get_review_history()
        self.assertEqual(len(all_history), 2)

        day1_history = db.get_review_history(day=1)
        self.assertEqual(len(day1_history), 2)

        limited = db.get_review_history(limit=1)
        self.assertEqual(len(limited), 1)
        db.close()


if __name__ == "__main__":
    unittest.main()
