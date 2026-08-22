"""AI Engineer Training Platform - 核心平台模块"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class EvaluationResult:
    """统一评测结果"""
    day: int
    submission_path: str
    syntax_valid: bool
    execution_success: bool
    execution_time: float
    tests_total: int
    tests_passed: int
    tests_failed: int
    tests_errors: int
    test_score: float
    ai_available: bool
    ai_score: Optional[float]
    final_score: float
    test_details: list
    ai_review: Optional[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "day": self.day,
            "submission_path": self.submission_path,
            "syntax_valid": self.syntax_valid,
            "execution_success": self.execution_success,
            "execution_time": self.execution_time,
            "tests_total": self.tests_total,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "tests_errors": self.tests_errors,
            "test_score": self.test_score,
            "ai_available": self.ai_available,
            "ai_score": self.ai_score,
            "final_score": self.final_score,
            "test_details": self.test_details,
            "ai_review": self.ai_review
        }


class TrainingPlatform:
    """AI训练平台"""
    
    def __init__(self):
        from src.task_manager import TaskManager
        from src.evaluator import CodeExecutor
        from src.agents import DeepSeekAgent, LearningAgent
        from src.database import Database
        from src.llm import LLMClient
        from src.rag import KnowledgeBase
        from src.submission_manager import SubmissionManager
        from src.utils.helpers import Helpers
        
        self.task_manager = TaskManager()
        self.code_executor = CodeExecutor()
        self.llm_client = LLMClient()
        self.deepseek_agent = DeepSeekAgent(self.llm_client)
        self.learning_agent = LearningAgent(self.llm_client)
        self.database = Database()
        self.submission_manager = SubmissionManager()
        self.knowledge_base = KnowledgeBase()
        self.helpers = Helpers
        
        self.current_day = 1
        self.user_name = "学员"
    
    def evaluate_submission(self, day: int, submission_path: Path) -> EvaluationResult:
        """评测提交的代码"""
        from src.evaluator import TestEngine
        
        submission_path = Path(submission_path)
        
        # 1. 读取代码
        try:
            with open(submission_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception:
            return self._create_error_result(day, submission_path)
        
        # 2. 语法检查
        validation = self.code_executor.validate_code(code)
        syntax_valid = validation["valid"]
        
        # 3. 执行检查
        execution_success = False
        execution_time = 0.0
        
        if syntax_valid:
            exec_result = self.code_executor.execute_code(code)
            execution_success = exec_result.status == "success"
            execution_time = exec_result.time
        
        # 4. 运行测试
        test_engine = TestEngine()
        test_result = test_engine.run_submission(day, submission_path)
        
        test_score = test_result.score
        
        # 5. AI Review
        ai_available = False
        ai_score = None
        ai_review = None
        
        task = self.task_manager.get_task(day)
        
        if self.llm_client.is_available():
            try:
                review_result = self.deepseek_agent.review_code(
                    code=code,
                    task_description=task.description if task else "",
                    test_results=json.dumps(test_result.to_dict()),
                    test_score=test_score,
                    day=day,
                    task_title=task.title if task else "",
                    tests_passed=test_result.passed,
                    tests_failed=test_result.failed,
                    tests_errors=test_result.errors,
                    error_messages=[t.message for t in test_result.test_results if t.status == "error"]
                )
                ai_available = True
                ai_score = review_result.score
                ai_review = review_result.to_dict()
            except Exception:
                pass
        
        # 6. 计算最终分数
        final_score = self._calculate_final_score(
            syntax_valid=syntax_valid,
            execution_success=execution_success,
            test_score=test_score,
            ai_score=ai_score,
            ai_available=ai_available,
            tests_total=test_result.total_tests,
            tests_passed=test_result.passed
        )
        
        return EvaluationResult(
            day=day,
            submission_path=str(submission_path),
            syntax_valid=syntax_valid,
            execution_success=execution_success,
            execution_time=execution_time,
            tests_total=test_result.total_tests,
            tests_passed=test_result.passed,
            tests_failed=test_result.failed,
            tests_errors=test_result.errors,
            test_score=test_score,
            ai_available=ai_available,
            ai_score=ai_score,
            final_score=final_score,
            test_details=[t.to_dict() for t in test_result.test_results],
            ai_review=ai_review
        )
    
    def _create_error_result(self, day: int, submission_path: Path) -> EvaluationResult:
        """创建错误结果"""
        return EvaluationResult(
            day=day,
            submission_path=str(submission_path),
            syntax_valid=False,
            execution_success=False,
            execution_time=0.0,
            tests_total=0,
            tests_passed=0,
            tests_failed=0,
            tests_errors=0,
            test_score=0.0,
            ai_available=False,
            ai_score=None,
            final_score=0.0,
            test_details=[],
            ai_review=None
        )
    
    def _calculate_final_score(self, syntax_valid, execution_success, test_score,
                               ai_score, ai_available, tests_total, tests_passed):
        """计算最终分数"""
        if not syntax_valid or not execution_success:
            return 0.0
        
        if tests_total > 0:
            pass_rate = tests_passed / tests_total
            if pass_rate < 0.5:
                return min(test_score, 59.0)
        
        if ai_available and ai_score is not None:
            return round(test_score * 0.7 + ai_score * 0.3, 1)
        
        return test_score
    
    def get_task(self, day: int):
        return self.task_manager.get_task(day)
    
    def get_progress(self, day: int):
        return self.database.get_progress(day)
    
    def get_all_progress(self):
        return self.database.get_all_progress()
    
    def get_statistics(self):
        return self.database.get_learning_statistics()
    
    def save_progress(self, evaluation_result: EvaluationResult):
        from src.database.db import ProgressRecord
        progress = ProgressRecord(
            day=evaluation_result.day,
            score=evaluation_result.final_score,
            test_result={
                "tests_total": evaluation_result.tests_total,
                "tests_passed": evaluation_result.tests_passed,
                "test_score": evaluation_result.test_score
            },
            ai_review=evaluation_result.ai_review or {}
        )
        self.database.save_progress(progress)