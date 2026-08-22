"""End-to-end tests for submission evaluation pipeline"""
import pytest
import tempfile
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def _create_test_file(tests_dir: Path):
    """Create a test file that imports from answer.py"""
    test_content = '''import pytest
from answer import add

def test_add_positive():
    assert add(1, 2) == 3

def test_add_negative():
    assert add(-1, -1) == -2

def test_add_zero():
    assert add(0, 0) == 0
'''
    test_file = tests_dir / "day01_test.py"
    test_file.write_text(test_content, encoding='utf-8')
    return test_file


class TestSubmissionPipeline:
    """Submission pipeline end-to-end tests"""
    
    def setup_method(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.tests_dir = self.test_dir / "tests"
        self.tests_dir.mkdir()
    
    def teardown_method(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_correct_code_passes(self):
        """Test 1: Correct code passes all tests"""
        _create_test_file(self.tests_dir)
        
        answer_file = self.test_dir / "answer.py"
        answer_file.write_text("def add(a, b):\n    return a + b\n", encoding='utf-8')
        
        from src.evaluator import TestEngine
        engine = TestEngine(tests_dir=str(self.tests_dir))
        
        result = engine.run_submission(1, answer_file)
        
        assert result.total_tests == 3
        assert result.passed == 3
        assert result.failed == 0
        assert result.score == 100.0
    
    def test_wrong_code_fails(self):
        """Test 2: Wrong code fails tests"""
        _create_test_file(self.tests_dir)
        
        answer_file = self.test_dir / "answer.py"
        answer_file.write_text("def add(a, b):\n    return a - b\n", encoding='utf-8')
        
        from src.evaluator import TestEngine
        engine = TestEngine(tests_dir=str(self.tests_dir))
        
        result = engine.run_submission(1, answer_file)
        
        assert result.total_tests == 3
        assert result.passed < 3
        assert result.failed > 0
        assert result.score < 100.0
    
    def test_syntax_error(self):
        """Test 3: Syntax error detected"""
        from src.evaluator import CodeExecutor
        executor = CodeExecutor()
        
        code = "def add(\n"
        validation = executor.validate_code(code)
        
        assert validation["valid"] is False
    
    def test_timeout(self):
        """Test 4: Infinite loop causes timeout"""
        _create_test_file(self.tests_dir)
        
        answer_file = self.test_dir / "answer.py"
        answer_file.write_text("def add(a, b):\n    while True: pass\n", encoding='utf-8')
        
        from src.evaluator import TestEngine
        engine = TestEngine(tests_dir=str(self.tests_dir), timeout=3)
        
        result = engine.run_submission(1, answer_file)
        
        assert result.errors >= 1 or result.duration >= 3.0
    
    def test_missing_test_file(self):
        """Test 5: Missing test file returns error"""
        answer_file = self.test_dir / "answer.py"
        answer_file.write_text("def add(a, b):\n    return a + b\n", encoding='utf-8')
        
        from src.evaluator import TestEngine
        engine = TestEngine(tests_dir=str(self.tests_dir))
        
        result = engine.run_submission(99, answer_file)
        
        assert result.total_tests == 0
        assert result.errors == 1
        assert result.score == 0.0


class TestFinalScoreCalculation:
    """Final score calculation tests"""
    
    def test_syntax_error_gives_zero(self):
        from src.core.platform import TrainingPlatform
        platform = TrainingPlatform()
        
        score = platform._calculate_final_score(
            syntax_valid=False, execution_success=False,
            timeout=False, test_score=80.0, ai_score=90.0, ai_available=True
        )
        assert score == 0.0
    
    def test_timeout_gives_zero(self):
        from src.core.platform import TrainingPlatform
        platform = TrainingPlatform()
        
        score = platform._calculate_final_score(
            syntax_valid=True, execution_success=True,
            timeout=True, test_score=80.0, ai_score=90.0, ai_available=True
        )
        assert score == 0.0
    
    def test_normal_scoring(self):
        from src.core.platform import TrainingPlatform
        platform = TrainingPlatform()
        
        score = platform._calculate_final_score(
            syntax_valid=True, execution_success=True,
            timeout=False, test_score=80.0, ai_score=90.0, ai_available=True
        )
        assert score == 83.0
    
    def test_no_ai_uses_test_only(self):
        from src.core.platform import TrainingPlatform
        platform = TrainingPlatform()
        
        score = platform._calculate_final_score(
            syntax_valid=True, execution_success=True,
            timeout=False, test_score=80.0, ai_score=None, ai_available=False
        )
        assert score == 80.0


class TestRunTestsRequiresFile:
    """run_tests() must require test_file"""
    
    def test_run_tests_without_file_fails(self):
        from src.evaluator import TestEngine
        engine = TestEngine()
        
        result = engine.run_tests(None)
        
        assert result.errors == 1
        assert "required" in result.test_results[0].message.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
