"""AI Engineer Training Platform - Core module"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.evaluator.models import EvaluationResult


class TrainingPlatform:
    """AI Training Platform"""
    
    def __init__(self):
        from src.task_manager import TaskManager
        from src.evaluator import CodeExecutor, TestEngine
        from src.agents import DeepSeekAgent, LearningAgent
        from src.database import Database
        from src.llm import LLMClient
        from src.rag import KnowledgeBase
        from src.submission_manager import SubmissionManager
        from src.utils.helpers import Helpers
        
        self.task_manager = TaskManager()
        self.code_executor = CodeExecutor()
        self.test_engine = TestEngine()
        self.llm_client = LLMClient()
        self.deepseek_agent = DeepSeekAgent(self.llm_client)
        self.learning_agent = LearningAgent(self.llm_client)
        self.database = Database()
        self.submission_manager = SubmissionManager()
        self.knowledge_base = KnowledgeBase()
        self.helpers = Helpers
        
        self.current_day = 1
        self.user_name = "Student"
    
    def evaluate_submission(self, day: int, submission_path: Path) -> EvaluationResult:
        """Evaluate submitted code"""
        submission_path = Path(submission_path)
        
        # 1. Read code
        try:
            with open(submission_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception:
            return self._create_error_result(day, submission_path, timeout=False)
        
        # 2. Syntax check
        validation = self.code_executor.validate_code(code)
        syntax_valid = validation["valid"]
        
        # 3. Execution check
        execution_success = False
        if syntax_valid:
            exec_result = self.code_executor.execute_code(code)
            execution_success = exec_result.status == "success"
        
        # 4. Run tests
        test_result = self.test_engine.run_submission(day, submission_path)
        test_score = test_result.score
        timeout = test_result.timeout if hasattr(test_result, 'timeout') else False
        
        # 5. AI Review
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
                ai_score = review_result.score
                ai_review = review_result.to_dict()
            except Exception:
                pass
        
        # 6. Calculate final score
        final_score = self._calculate_final_score(
            syntax_valid=syntax_valid,
            execution_success=execution_success,
            timeout=timeout,
            test_score=test_score,
            ai_score=ai_score,
            ai_available=ai_score is not None
        )
        
        return EvaluationResult(
            day=day,
            submission_path=str(submission_path),
            syntax_valid=syntax_valid,
            execution_success=execution_success,
            timeout=timeout,
            tests_total=test_result.total_tests,
            tests_passed=test_result.passed,
            test_score=test_score,
            ai_score=ai_score,
            final_score=final_score,
            ai_review=ai_review
        )
    
    def _create_error_result(self, day: int, submission_path: Path, timeout: bool = False) -> EvaluationResult:
        """Create error result"""
        return EvaluationResult(
            day=day,
            submission_path=str(submission_path),
            syntax_valid=False,
            execution_success=False,
            timeout=timeout,
            tests_total=0,
            tests_passed=0,
            test_score=0.0,
            ai_score=None,
            final_score=0.0,
            ai_review=None
        )
    
    def _calculate_final_score(self, syntax_valid: bool, execution_success: bool,
                               timeout: bool, test_score: float, ai_score: Optional[float],
                               ai_available: bool) -> float:
        """Calculate final score
        
        Rules:
        - Syntax error: 0
        - Timeout: 0
        - Normal: test_score * 0.7 + ai_score * 0.3
        - No AI: test_score only
        """
        if not syntax_valid or not execution_success or timeout:
            return 0.0
        
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
        """Save evaluation result"""
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
        
        # Save evaluation log
        log_dir = Path("logs/evaluations")
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"day{evaluation_result.day:02d}_{timestamp}.json"
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(evaluation_result.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception:
            pass
