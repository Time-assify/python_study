"""Integration tests for Learning Profile Pipeline"""
import json
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import LearningRecord, StudentProfile, ReviewResult
from src.database.db import Database
from src.agents.code_review_agent import CodeReviewAgent
from src.agents.learning_advisor import LearningAdvisor
from src.analyzer import ErrorClassifier


class TestLearningPipelineIntegration:
    """完整Pipeline集成测试"""

    def setup_method(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_dir, "test.db")
        self.db = Database(self.db_path)

    def teardown_method(self):
        self.db.close()
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_submission_history_persistence(self):
        """测试Case A: 提交记录正确持久化到数据库"""
        record = LearningRecord(
            day=1,
            task_id="1",
            submission_path="submissions/day01/answer.py",
            test_score=85.0,
            ai_score=78.0,
            final_score=82.9,
            errors=[{"test_name": "test1", "message": "failed", "error_type": "LogicError"}],
            knowledge_gaps=["Tensor维度"],
            suggestions=["多练习"]
        )
        record_id = self.db.save_submission_history(record)
        assert record_id > 0

        # 验证数据完整写入
        history = self.db.get_submission_history(day=1)
        assert len(history) == 1
        h = history[0]
        assert h["day"] == 1
        assert h["test_score"] == 85.0
        assert h["ai_score"] == 78.0
        assert h["final_score"] == 82.9
        assert h["errors"][0]["error_type"] == "LogicError"
        assert h["knowledge_gaps"] == ["Tensor维度"]
        assert h["suggestions"] == ["多练习"]

    def test_review_history_persistence(self):
        """测试: review记录正确持久化"""
        review_result = {
            "score": 80,
            "summary": "Good",
            "strengths": ["代码清晰"],
            "issues": ["命名不规范"],
            "knowledge_gaps": ["训练循环"],
            "improvement": ["多练习"],
            "next_learning": ["PyTorch"]
        }
        record_id = self.db.save_review_history(day=1, code_snippet="def foo(): pass", review_result=review_result)
        assert record_id > 0

        history = self.db.get_review_history(day=1)
        assert len(history) == 1
        assert history[0]["review_result"]["score"] == 80
        assert history[0]["review_result"]["knowledge_gaps"] == ["训练循环"]

    def test_ai_unavailable_score_is_none(self):
        """测试Case B: AI不可用时 ai_score=None，最终分数=test_score"""
        mock_llm = MagicMock()
        mock_llm.is_available.return_value = False
        agent = CodeReviewAgent(mock_llm)

        result = agent.review(
            day=1, code="test", task={}, requirement="",
            pytest_result={}, profile=StudentProfile()
        )

        assert result.score is None
        assert result.review_status == "fallback"

        # 验证：AI不可用时，platform不会将70分参与评分
        # 模拟platform逻辑
        ai_score = None
        if result.review_status == "success" and result.score is not None:
            ai_score = result.score
        assert ai_score is None

    def test_profile_error_and_knowledge_gap_separation(self):
        """测试Case C: error_statistics和knowledge_gap_statistics分离"""
        # 添加带errors的提交
        for i in range(3):
            record = LearningRecord(
                day=i+1, task_id=str(i+1), test_score=80.0, final_score=80.0,
                errors=[
                    {"test_name": "test", "message": "shape error", "error_type": "TensorShapeError"},
                    {"test_name": "test2", "message": "import error", "error_type": "ImportError"}
                ]
            )
            self.db.save_submission_history(record)

        # 添加带knowledge_gaps的review
        review_result = {"knowledge_gaps": ["Tensor维度", "Tensor维度", "训练循环"], "strengths": ["代码规范"]}
        self.db.save_review_history(day=1, code_snippet="test", review_result=review_result)

        # 验证分离
        error_stats = self.db.get_error_statistics()
        kg_stats = self.db.get_knowledge_gap_statistics()

        assert error_stats.get("TensorShapeError", 0) == 3
        assert error_stats.get("ImportError", 0) == 3
        assert kg_stats.get("Tensor维度", 0) == 2
        assert kg_stats.get("训练循环", 0) == 1

    def test_history_format_for_prompt(self):
        """测试Case D: 历史记录格式匹配CodeReviewAgent._build_prompt期望"""
        # 第一次提交
        record1 = LearningRecord(
            day=1, task_id="1", test_score=70.0, final_score=70.0,
            errors=[
                {"test_name": "test_matmul", "message": "mat1 and mat2 shapes cannot be multiplied", "error_type": "TensorShapeError"}
            ]
        )
        self.db.save_submission_history(record1)

        # 模拟_get_error_history读取
        history = []
        submissions = self.db.get_submission_history(limit=50)
        for sub in submissions:
            if sub["day"] < 2 and sub.get("errors"):
                for err in sub["errors"]:
                    history.append({
                        "day": sub["day"],
                        "error_type": err.get("error_type", "Unknown"),
                        "message": err.get("message", "")[:200],
                        "test_score": sub["test_score"]
                    })

        assert len(history) == 1
        assert history[0]["day"] == 1
        assert history[0]["error_type"] == "TensorShapeError"
        assert "mat1 and mat2" in history[0]["message"]
        assert history[0]["test_score"] == 70.0

    def test_update_profile_comprehensive(self):
        """测试update_profile返回完整画像"""
        # 添加数据
        for i in range(3):
            record = LearningRecord(
                day=i+1, task_id=str(i+1), test_score=80.0+i*5, final_score=80.0+i*5,
                errors=[{"test_name": "test", "message": "err", "error_type": "SyntaxError"}]
            )
            self.db.save_submission_history(record)

        review_result = {"knowledge_gaps": ["Python语法", "Python语法"], "strengths": ["代码结构清晰"]}
        self.db.save_review_history(day=1, code_snippet="test", review_result=review_result)

        profile = self.db.update_profile()
        assert profile["total_submissions"] == 3
        assert profile["average_score"] > 0
        assert "SyntaxError" in profile["error_statistics"]
        assert "Python语法" in profile["knowledge_gap_statistics"]
        assert len(profile["weaknesses"]) > 0
        assert len(profile["strengths"]) > 0
        assert profile["trend"] in ("improving", "stable", "declining")
