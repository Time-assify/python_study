"""Unified test loader for submission evaluation"""
import shutil
import tempfile
import os
from pathlib import Path
from typing import Optional


class TestLoader:
    """Test environment loader for submission evaluation"""
    
    def __init__(self, tests_dir: str = "tests"):
        self.tests_dir = Path(tests_dir)
    
    def load_test_environment(self, day: int, submission_path: str) -> Optional[Path]:
        """Prepare test environment for submission evaluation
        
        Args:
            day: Day number (1-40)
            submission_path: Path to user's answer.py
            
        Returns:
            Temporary directory path or None if setup fails
        """
        test_file = self.tests_dir / f"day{day:02d}_test.py"
        submission = Path(submission_path)
        
        if not test_file.exists():
            return None
        
        if not submission.exists():
            return None
        
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            shutil.copy2(submission, temp_dir / "answer.py")
            shutil.copy2(test_file, temp_dir / test_file.name)
            return temp_dir
        except Exception:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None
    
    def get_test_file(self, day: int) -> Optional[Path]:
        """Get test file for specific day"""
        test_file = self.tests_dir / f"day{day:02d}_test.py"
        return test_file if test_file.exists() else None
    
    def cleanup(self, temp_dir: Path):
        """Clean up temporary directory"""
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
