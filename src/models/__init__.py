"""Unified Models - 所有模块统一使用此目录下的模型"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
from datetime import datetime


@dataclass
class LearningRecord:
    """统一学习记录 - 所有模块使用此对象"""
    id: Optional[int] = None
    day: int = 0
    task_id: str = ""
    submission_path: str = ""
    test_score: float = 0.0
    ai_score: Optional[float] = None
    final_score: float = 0.0
    errors: List[Dict[str, Any]] = None
    knowledge_gaps: List[str] = None
    suggestions: List[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.knowledge_gaps is None:
            self.knowledge_gaps = []
        if self.suggestions is None:
            self.suggestions = []
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StudentProfile:
    """学生画像"""
    total_submissions: int = 0
    average_score: float = 0.0
    error_statistics: Dict[str, int] = None
    knowledge_gap_statistics: Dict[str, int] = None
    weaknesses: List[str] = None
    strengths: List[str] = None
    trend: str = "stable"

    def __post_init__(self):
        if self.error_statistics is None:
            self.error_statistics = {}
        if self.knowledge_gap_statistics is None:
            self.knowledge_gap_statistics = {}
        if self.weaknesses is None:
            self.weaknesses = []
        if self.strengths is None:
            self.strengths = []

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReviewResult:
    """代码审查结果（统一名称，替代CodeReviewResult）"""
    score: Optional[float] = None
    summary: str = ""
    strengths: List[str] = None
    issues: List[str] = None
    knowledge_gaps: List[str] = None
    improvement: List[str] = None
    next_learning: List[str] = None
    day: int = 0
    review_status: str = "success"

    def __post_init__(self):
        if self.strengths is None:
            self.strengths = []
        if self.issues is None:
            self.issues = []
        if self.knowledge_gaps is None:
            self.knowledge_gaps = []
        if self.improvement is None:
            self.improvement = []
        if self.next_learning is None:
            self.next_learning = []

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvaluationResult:
    """统一评估结果"""
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
