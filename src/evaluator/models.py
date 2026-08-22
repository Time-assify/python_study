"""Evaluation models - imports from unified models"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional

from src.models import EvaluationResult


@dataclass
class TestResult:
    """Single test result"""
    test_name: str
    status: str  # passed, failed, error
    duration: float
    message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TestSuiteResult:
    """Test suite results"""
    total_tests: int
    passed: int
    failed: int
    errors: int
    duration: float
    test_results: List[TestResult]
    score: float = 0.0
    timeout: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "duration": self.duration,
            "score": self.score,
            "timeout": self.timeout,
            "test_results": [t.to_dict() for t in self.test_results]
        }
