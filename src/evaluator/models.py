"""Unified evaluation models"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional


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
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "duration": self.duration,
            "score": self.score,
            "test_results": [t.to_dict() for t in self.test_results]
        }


@dataclass
class EvaluationResult:
    """Unified evaluation result"""
    day: int
    submission_path: str
    syntax_valid: bool
    execution_success: bool
    timeout: bool
    tests_total: int
    tests_passed: int
    test_score: float
    ai_score: Optional[float]
    final_score: float
    ai_review: Optional[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "day": self.day,
            "submission_path": self.submission_path,
            "syntax_valid": self.syntax_valid,
            "execution_success": self.execution_success,
            "timeout": self.timeout,
            "tests_total": self.tests_total,
            "tests_passed": self.tests_passed,
            "test_score": self.test_score,
            "ai_score": self.ai_score,
            "final_score": self.final_score,
            "ai_review": self.ai_review
        }
