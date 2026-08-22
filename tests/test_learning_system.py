# Learning System Tests
import pytest
import sys
import os
from pathlib import Path

# 添加项目根目录和src目录到路径
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))


class TestLearningSystem:
    """学习系统测试"""

    def test_import_learning_system(self):
        from learning_system import LearningSystem
        assert LearningSystem is not None

    def test_phase_info(self):
        from src.utils.helpers import Helpers
        phase1 = Helpers.get_phase_info(1)
        assert phase1["phase"] == 1
        assert phase1["name"] == "Python工程"

        phase2 = Helpers.get_phase_info(10)
        assert phase2["phase"] == 2

        phase3 = Helpers.get_phase_info(20)
        assert phase3["phase"] == 3

        phase4 = Helpers.get_phase_info(35)
        assert phase4["phase"] == 4


class TestSubmissionManager:
    """提交管理器测试"""

    def test_submit_code(self):
        import tempfile, shutil
        from src.submission_manager import SubmissionManager

        test_dir = tempfile.mkdtemp()
        try:
            manager = SubmissionManager(submissions_dir=test_dir)
            submission = manager.submit_code(day=1, code="print('hello')", score=85.0)
            assert submission.day == 1
            assert submission.score == 85.0
        finally:
            shutil.rmtree(test_dir)

    def test_get_submissions(self):
        import tempfile, shutil
        from src.submission_manager import SubmissionManager

        test_dir = tempfile.mkdtemp()
        try:
            manager = SubmissionManager(submissions_dir=test_dir)
            manager.submit_code(day=1, code="test1", score=80)
            manager.submit_code(day=1, code="test2", score=90)
            submissions = manager.get_submissions(1)
            assert len(submissions) == 2
        finally:
            shutil.rmtree(test_dir)


class TestKnowledgeBase:
    """知识库测试"""

    def test_add_and_search(self):
        import tempfile, shutil
        from src.rag import KnowledgeBase

        test_dir = tempfile.mkdtemp()
        try:
            kb = KnowledgeBase(persist_dir=test_dir)
            kb.add_text("Python is a programming language", source="test")
            kb.add_text("Machine learning is a branch of AI", source="test")
            results = kb.search("Python")
            assert len(results) > 0
        finally:
            shutil.rmtree(test_dir)


class TestCodeExecutor:
    """代码执行器测试"""

    def test_execute_code(self):
        from src.evaluator import CodeExecutor
        executor = CodeExecutor()
        result = executor.execute_code("print('hello')")
        assert result.status == "success"
        assert "hello" in result.stdout

    def test_validate_code(self):
        from src.evaluator import CodeExecutor
        executor = CodeExecutor()
        valid = executor.validate_code("x = 1")
        assert valid["valid"] is True

        invalid = executor.validate_code("def foo(")
        assert invalid["valid"] is False


class TestDatabase:
    """数据库测试"""

    def test_save_and_get_progress(self):
        import tempfile, os
        from src.database import Database
        from src.database.db import ProgressRecord

        db_path = os.path.join(tempfile.mkdtemp(), "test.db")
        db = Database(db_path)
        try:
            progress = ProgressRecord(day=1, score=85.0, test_result={}, ai_review={})
            db.save_progress(progress)

            loaded = db.get_progress(1)
            assert loaded is not None
            assert loaded.day == 1
            assert loaded.score == 85.0
        finally:
            db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])