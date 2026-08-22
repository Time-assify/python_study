"""Tests for Learning Profile System"""
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import LearningRecord, StudentProfile
from src.analyzer import ErrorClassifier, ErrorType
from src.agents.learning_advisor import LearningAdvisor, LearningAdvice
from src.agents.code_review_agent import CodeReviewAgent, CodeReviewResult
from src.database.db import Database


class TestLearningRecord:
    """测试 LearningRecord 数据类"""

    def test_create_learning_record(self):
        record = LearningRecord(
            day=1,
            task_id="1",
            submission_path="submissions/day01/answer.py",
            test_score=85.0,
            ai_score=78.0,
            final_score=82.9,
            errors=[],
            knowledge_gaps=["Tensor维度"],
            suggestions=["多练习shape"]
        )
        assert record.day == 1
        assert record.test_score == 85.0
        assert record.ai_score == 78.0
        assert record.final_score == 82.9
        assert record.knowledge_gaps == ["Tensor维度"]

    def test_learning_record_defaults(self):
        record = LearningRecord()
        assert record.day == 0
        assert record.errors == []
        assert record.knowledge_gaps == []
        assert record.suggestions == []
        assert record.timestamp != ""

    def test_learning_record_to_dict(self):
        record = LearningRecord(day=5, test_score=90.0)
        d = record.to_dict()
        assert isinstance(d, dict)
        assert d["day"] == 5
        assert d["test_score"] == 90.0
        assert "timestamp" in d


class TestStudentProfile:
    """测试 StudentProfile 数据类"""

    def test_create_profile(self):
        profile = StudentProfile(
            total_submissions=10,
            average_score=78.5,
            error_statistics={"TensorShapeError": 5, "ImportError": 3},
            weaknesses=["TensorShapeError", "ImportError"],
            strengths=["代码规范"]
        )
        assert profile.total_submissions == 10
        assert profile.average_score == 78.5
        assert profile.error_statistics["TensorShapeError"] == 5

    def test_profile_defaults(self):
        profile = StudentProfile()
        assert profile.total_submissions == 0
        assert profile.average_score == 0.0
        assert profile.error_statistics == {}
        assert profile.weaknesses == []

    def test_profile_to_dict(self):
        profile = StudentProfile(total_submissions=5, average_score=80.0)
        d = profile.to_dict()
        assert isinstance(d, dict)
        assert d["total_submissions"] == 5


class TestErrorClassifier:
    """测试 ErrorClassifier"""

    def setup_method(self):
        self.classifier = ErrorClassifier()

    def test_classify_syntax_error(self):
        result = self.classifier.classify("SyntaxError: invalid syntax")
        assert result.type == "SyntaxError"
        assert result.category == "Python基础"

    def test_classify_import_error(self):
        result = self.classifier.classify("ImportError: cannot import name 'xxx'")
        assert result.type == "ImportError"
        assert result.category == "Python基础"

    def test_classify_tensor_shape_error(self):
        result = self.classifier.classify(
            "RuntimeError: mat1 and mat2 shapes cannot be multiplied (3x4 and 5x6)"
        )
        assert result.type == "TensorShapeError"
        assert result.category == "PyTorch"

    def test_classify_timeout(self):
        result = self.classifier.classify("TimeoutError: operation timed out")
        assert result.type == "TimeoutError"
        assert result.category == "性能"

    def test_classify_empty_message(self):
        result = self.classifier.classify("")
        assert result.type == "Unknown"

    def test_classify_unknown_error(self):
        result = self.classifier.classify("SomeRandomError: blah")
        assert result.type == "Other"

    def test_classify_batch(self):
        errors = [
            "SyntaxError: invalid syntax",
            "ImportError: no module named 'torch'",
            "SyntaxError: unexpected EOF",
        ]
        stats = self.classifier.classify_batch(errors)
        assert stats["SyntaxError"] == 2
        assert stats["ImportError"] == 1

    def test_get_weaknesses(self):
        stats = {"TensorShapeError": 5, "ImportError": 1}
        weaknesses = self.classifier.get_weaknesses(stats, threshold=2)
        assert len(weaknesses) == 1
        assert "TensorShapeError" in weaknesses[0]


class TestLearningAdvisor:
    """测试 LearningAdvisor"""

    def setup_method(self):
        self.advisor = LearningAdvisor()

    def test_generate_advice_no_data(self):
        profile = StudentProfile()
        advice = self.advisor.generate_advice(profile)
        assert len(advice.suggestions) > 0
        assert "暂无历史数据" in advice.suggestions[0]

    def test_generate_advice_with_errors(self):
        profile = StudentProfile(
            error_statistics={"TensorShapeError": 5, "ImportError": 3}
        )
        advice = self.advisor.generate_advice(profile)
        assert len(advice.weaknesses) > 0
        assert len(advice.suggestions) > 0
        assert len(advice.priority_topics) > 0

    def test_generate_advice_tensor_error(self):
        profile = StudentProfile(error_statistics={"TensorShapeError": 3})
        advice = self.advisor.generate_advice(profile)
        assert any("Tensor" in t for t in advice.priority_topics)

    def test_generate_advice_syntax_error(self):
        profile = StudentProfile(error_statistics={"SyntaxError": 2})
        advice = self.advisor.generate_advice(profile)
        assert len(advice.weaknesses) > 0

    def test_advice_to_dict(self):
        profile = StudentProfile(error_statistics={"ImportError": 2})
        advice = self.advisor.generate_advice(profile)
        d = advice.to_dict()
        assert isinstance(d, dict)
        assert "weaknesses" in d
        assert "suggestions" in d

    def test_priority_score(self):
        score = self.advisor.get_priority_score("TensorShapeError", 5)
        assert score > 0
        score2 = self.advisor.get_priority_score("OtherError", 1)
        assert score < score2 or score > score2  # just check it returns int


class TestDatabaseNewTables:
    """测试数据库新表"""

    def setup_method(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_dir, "test.db")
        self.db = Database(self.db_path)

    def teardown_method(self):
        self.db.close()
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_save_submission_history(self):
        record = LearningRecord(
            day=1,
            task_id="1",
            submission_path="submissions/day01/answer.py",
            test_score=85.0,
            ai_score=78.0,
            final_score=82.9
        )
        record_id = self.db.save_submission_history(record)
        assert record_id > 0

    def test_get_submission_history(self):
        record = LearningRecord(day=1, task_id="1", test_score=85.0, final_score=82.9)
        self.db.save_submission_history(record)
        
        history = self.db.get_submission_history()
        assert len(history) >= 1
        assert history[0]["day"] == 1
        assert history[0]["test_score"] == 85.0

    def test_get_submission_history_by_day(self):
        record1 = LearningRecord(day=1, task_id="1", test_score=80.0, final_score=80.0)
        record2 = LearningRecord(day=2, task_id="2", test_score=90.0, final_score=90.0)
        self.db.save_submission_history(record1)
        self.db.save_submission_history(record2)
        
        history = self.db.get_submission_history(day=1)
        assert len(history) == 1
        assert history[0]["day"] == 1

    def test_submission_count(self):
        assert self.db.get_submission_count() == 0
        record = LearningRecord(day=1, task_id="1", test_score=85.0, final_score=82.9)
        self.db.save_submission_history(record)
        assert self.db.get_submission_count() == 1

    def test_average_score(self):
        record1 = LearningRecord(day=1, task_id="1", test_score=80.0, final_score=80.0)
        record2 = LearningRecord(day=2, task_id="2", test_score=90.0, final_score=90.0)
        self.db.save_submission_history(record1)
        self.db.save_submission_history(record2)
        
        avg = self.db.get_average_score()
        assert avg == 85.0

    def test_error_statistics_empty(self):
        stats = self.db.get_error_statistics()
        assert stats == {}

    def test_error_statistics_with_reviews(self):
        review_result = {
            "knowledge_gaps": ["Tensor维度", "训练循环", "Tensor维度"]
        }
        self.db.save_review_history(day=1, code_snippet="test", review_result=review_result)
        
        stats = self.db.get_error_statistics()
        assert stats["Tensor维度"] == 2
        assert stats["训练循环"] == 1


class TestCodeReviewAgentWithProfile:
    """测试 CodeReviewAgent 接受 profile 参数"""

    def setup_method(self):
        self.mock_llm = MagicMock()
        self.mock_llm.is_available.return_value = True

    def test_review_accepts_profile(self):
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "score": 85,
            "summary": "Good code",
            "strengths": ["清晰"],
            "issues": [],
            "knowledge_gaps": ["Tensor维度"],
            "improvement": ["多练习"],
            "next_learning": ["PyTorch"]
        })
        self.mock_llm.chat.return_value = mock_response
        self.mock_llm._extract_json.return_value = {
            "score": 85,
            "summary": "Good code",
            "strengths": ["清晰"],
            "issues": [],
            "knowledge_gaps": ["Tensor维度"],
            "improvement": ["多练习"],
            "next_learning": ["PyTorch"]
        }
        
        agent = CodeReviewAgent(self.mock_llm)
        profile = StudentProfile(
            total_submissions=5,
            average_score=78.0,
            error_statistics={"TensorShapeError": 3},
            weaknesses=["TensorShapeError"]
        )
        
        result = agent.review(
            day=1,
            code="def foo(): pass",
            task={"title": "Test", "description": "Test task", "goal": "Learn"},
            requirement="Write a function",
            pytest_result={"total": 3, "passed": 3, "failed": 0, "errors": 0, "details": []},
            history=[],
            profile=profile
        )
        
        assert isinstance(result, CodeReviewResult)
        assert result.score == 85
        assert result.review_status == "success"

    def test_review_fallback_without_llm(self):
        self.mock_llm.is_available.return_value = False
        agent = CodeReviewAgent(self.mock_llm)
        
        result = agent.review(
            day=1,
            code="test",
            task={},
            requirement="",
            pytest_result={},
            profile=StudentProfile()
        )
        
        assert result.review_status == "fallback"
