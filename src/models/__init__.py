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
class KnowledgeGapRecord:
    """知识点缺口记录（P0-1: 测试失败→skill→knowledge_point绑定）

    - skill:            skill标签（如 python.decorator）
    - knowledge_point:  {"id": skill, "name": 中文知识点名}
    - review_point:     兼容字段（上一轮review_points设计保留）
    - count:            累计失败次数
    """
    skill: str = ""
    knowledge_point: Optional[Dict[str, str]] = None
    review_point: str = ""
    count: int = 0

    def __post_init__(self):
        if self.knowledge_point is None and self.skill:
            self.knowledge_point = {"id": self.skill, "name": self.skill}

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def merge(self, other: "KnowledgeGapRecord") -> "KnowledgeGapRecord":
        """同(skill, review_point)合并计数，knowledge_point取自身优先"""
        if self.skill != other.skill or self.review_point != other.review_point:
            raise ValueError("cannot merge KnowledgeGapRecord with different keys")
        kp = self.knowledge_point or other.knowledge_point
        return KnowledgeGapRecord(self.skill, kp, self.review_point,
                                  self.count + other.count)


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
