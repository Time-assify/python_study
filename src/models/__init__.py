"""Learning Record Models - 统一学习记录模型"""
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
    weaknesses: List[str] = None
    strengths: List[str] = None

    def __post_init__(self):
        if self.error_statistics is None:
            self.error_statistics = {}
        if self.weaknesses is None:
            self.weaknesses = []
        if self.strengths is None:
            self.strengths = []

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
