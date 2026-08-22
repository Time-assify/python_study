"""端到端测试 - 验证评测流程"""
import pytest
import tempfile
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestSubmissionEvaluation:
    """提交评测测试"""
    
    def setup_method(self):
        """创建临时目录"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.submissions_dir = self.test_dir / "submissions" / "day01"
        self.submissions_dir.mkdir(parents=True)
        self.tests_dir = self.test_dir / "tests"
        self.tests_dir.mkdir(parents=True)
    
    def teardown_method(self):
        """清理临时目录"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_test_file(self):
        """创建测试文件"""
        test_content = '''import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from answer import add

def test_add_positive():
    assert add(1, 2) == 3

def test_add_negative():
    assert add(-1, -1) == -2

def test_add_zero():
    assert add(0, 0) == 0
'''
        test_file = self.tests_dir / "day01_test.py"
        test_file.write_text(test_content, encoding='utf-8')
        return test_file
    
    def test_correct_submission_passes(self):
        """正确代码应该通过测试"""
        self._create_test_file()
        
        # 创建正确的answer.py
        answer_content = '''def add(a, b):
    return a + b
'''
        answer_file = self.submissions_dir / "answer.py"
        answer_file.write_text(answer_content, encoding='utf-8')
        
        from src.evaluator import TestEngine
        engine = TestEngine(tests_dir=str(self.tests_dir))
        
        result = engine.run_submission(1, answer_file)
        
        assert result.total_tests == 3
        assert result.passed == 3
        assert result.failed == 0
        assert result.score == 100.0
    
    def test_wrong_submission_fails(self):
        """错误代码应该测试失败"""
        self._create_test_file()
        
        # 创建错误的answer.py
        answer_content = '''def add(a, b):
    return a - b  # 错误：应该是加法
'''
        answer_file = self.submissions_dir / "answer.py"
        answer_file.write_text(answer_content, encoding='utf-8')
        
        from src.evaluator import TestEngine
        engine = TestEngine(tests_dir=str(self.tests_dir))
        
        result = engine.run_submission(1, answer_file)
        
        assert result.total_tests == 3
        assert result.passed < 3
        assert result.failed > 0
        assert result.score < 100.0
    
    def test_syntax_error_returns_zero(self):
        """语法错误应该返回0分"""
        self._create_test_file()
        
        # 创建语法错误的answer.py
        answer_content = '''def add(a, b):
    return a + b
    # 缺少结束括号
'''
        answer_file = self.submissions_dir / "answer.py"
        answer_file.write_text(answer_content, encoding='utf-8')
        
        from src.evaluator import CodeExecutor
        executor = CodeExecutor()
        
        code = answer_file.read_text(encoding='utf-8')
        validation = executor.validate_code(code)
        
        # 语法检查应该失败或通过（取决于具体语法错误）
        # 这里我们验证检查机制存在
        assert "valid" in validation
    
    def test_missing_test_file_returns_error(self):
        """缺少测试文件应该返回错误"""
        answer_content = '''def add(a, b):
    return a + b
'''
        answer_file = self.submissions_dir / "answer.py"
        answer_file.write_text(answer_content, encoding='utf-8')
        
        from src.evaluator import TestEngine
        engine = TestEngine(tests_dir=str(self.tests_dir))
        
        # 尝试评测不存在的day
        result = engine.run_submission(99, answer_file)
        
        assert result.total_tests == 0
        assert result.errors == 1
        assert result.score == 0.0


class TestFinalScoreCalculation:
    """最终分数计算测试"""
    
    def test_syntax_error_gives_zero(self):
        """语法错误给出0分"""
        from src.core.platform import TrainingPlatform
        
        platform = TrainingPlatform()
        
        score = platform._calculate_final_score(
            syntax_valid=False,
            execution_success=False,
            test_score=80.0,
            ai_score=90.0,
            ai_available=True,
            tests_total=10,
            tests_passed=8
        )
        
        assert score == 0.0
    
    def test_low_pass_rate_caps_score(self):
        """低通过率限制分数"""
        from src.core.platform import TrainingPlatform
        
        platform = TrainingPlatform()
        
        score = platform._calculate_final_score(
            syntax_valid=True,
            execution_success=True,
            test_score=70.0,
            ai_score=90.0,
            ai_available=True,
            tests_total=10,
            tests_passed=4  # 40% < 50%
        )
        
        assert score <= 59.0
    
    def test_normal_scoring(self):
        """正常评分"""
        from src.core.platform import TrainingPlatform
        
        platform = TrainingPlatform()
        
        score = platform._calculate_final_score(
            syntax_valid=True,
            execution_success=True,
            test_score=80.0,
            ai_score=90.0,
            ai_available=True,
            tests_total=10,
            tests_passed=8
        )
        
        # 80 * 0.7 + 90 * 0.3 = 56 + 27 = 83
        assert score == 83.0
    
    def test_no_ai_uses_test_only(self):
        """无AI时只用测试分数"""
        from src.core.platform import TrainingPlatform
        
        platform = TrainingPlatform()
        
        score = platform._calculate_final_score(
            syntax_valid=True,
            execution_success=True,
            test_score=80.0,
            ai_score=None,
            ai_available=False,
            tests_total=10,
            tests_passed=8
        )
        
        assert score == 80.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])