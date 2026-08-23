"""Unified test loader for submission evaluation

TestLoader负责准备/清理隔离的测试环境。
TestEngine只负责运行pytest和解析结果。
"""
import shutil
import tempfile
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Optional


class TestLoader:
    """Test environment loader for submission evaluation"""
    
    def __init__(self, tests_dir: str = "tests"):
        self.tests_dir = Path(tests_dir)
    
    def get_test_file(self, day: int) -> Optional[Path]:
        """Get test file for specific day"""
        test_file = self.tests_dir / f"day{day:02d}_test.py"
        return test_file if test_file.exists() else None
    
    def load_test_environment(self, day: int, submission_path: str) -> Path:
        """Prepare isolated test environment
        
        Args:
            day: Day number (1-40)
            submission_path: Path to user's answer.py
            
        Returns:
            Temporary directory containing answer.py + dayXX_test.py
            
        Raises:
            FileNotFoundError: test file or submission missing
        """
        test_file = self.get_test_file(day)
        if test_file is None:
            raise FileNotFoundError(f"Test file not found: tests/day{day:02d}_test.py")
        
        submission = Path(submission_path)
        if not submission.exists():
            raise FileNotFoundError(f"Submission file not found: {submission_path}")
        
        temp_dir = Path(tempfile.mkdtemp())
        try:
            shutil.copy2(submission, temp_dir / "answer.py")
            shutil.copy2(test_file, temp_dir / test_file.name)
            return temp_dir
        except Exception:
            self.cleanup(temp_dir)
            raise
    
    @contextmanager
    def environment(self, day: int, submission_path: str):
        """Context manager yielding temp dir; guarantees cleanup
        
        Usage:
            with loader.environment(day, path) as env:
                pytest...
        """
        temp_dir = self.load_test_environment(day, submission_path)
        try:
            yield temp_dir
        finally:
            self.cleanup(temp_dir)
    
    def cleanup(self, temp_dir: Path):
        """Clean up temporary directory"""
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
