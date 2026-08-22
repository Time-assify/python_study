"""AI Engineer Training Platform - Core module"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.evaluator.models import EvaluationResult
from src.models import LearningRecord, StudentProfile
from src.agents.learning_advisor import LearningAdvisor
from src.analyzer import ErrorClassifier

logger = logging.getLogger(__name__)


class TrainingPlatform:
    """AI Training Platform"""
    
    def __init__(self):
        from src.task_manager import TaskManager
        from src.evaluator import CodeExecutor, TestEngine
        from src.agents import DeepSeekAgent, LearningAgent, CodeReviewAgent
        from src.database import Database
        from src.llm import DeepSeekClient
        from src.rag import KnowledgeBase
        from src.submission_manager import SubmissionManager
        from src.utils.helpers import Helpers
        
        self.task_manager = TaskManager()
        self.code_executor = CodeExecutor()
        self.test_engine = TestEngine()
        self.llm_client = DeepSeekClient()
        self.deepseek_agent = DeepSeekAgent(self.llm_client)
        self.learning_agent = LearningAgent(self.llm_client)
        self.code_review_agent = CodeReviewAgent(self.llm_client)
        self.database = Database()
        self.submission_manager = SubmissionManager()
        self.knowledge_base = KnowledgeBase()
        self.helpers = Helpers
        self.learning_advisor = LearningAdvisor()
        self.error_classifier = ErrorClassifier()
        
        self.current_day = 1
        self.user_name = "Student"
    
    def evaluate_submission(self, day: int, submission_path: Path) -> EvaluationResult:
        """Evaluate submitted code
        
        Pipeline:
        1. Syntax check
        2. Execution check
        3. Run tests (pytest)
        4. AI Code Review
        5. Calculate final score
        6. Save LearningRecord
        """
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
        
        # 5. Build student profile for personalized review
        profile = self._build_student_profile()
        
        # 6. AI Code Review (via CodeReviewAgent)
        ai_score = None
        ai_review = None
        
        task = self.task_manager.get_task(day)
        
        try:
            requirement_str = ""
            if task:
                requirement_str = getattr(task, 'task', '') or getattr(task, 'description', '')
            
            review_result = self.code_review_agent.review(
                day=day,
                code=code,
                task={
                    "title": task.title if task else "",
                    "description": task.description if task else "",
                    "goal": task.goal if task else ""
                },
                requirement=requirement_str,
                pytest_result={
                    "total": test_result.total_tests,
                    "passed": test_result.passed,
                    "failed": test_result.failed,
                    "errors": test_result.errors,
                    "details": [t.to_dict() for t in test_result.test_results]
                },
                history=self._get_error_history(day),
                profile=profile
            )
            ai_score = review_result.score
            ai_review = review_result.to_dict()
        except Exception as e:
            logger.warning("[evaluate_submission] AI review failed for day %d: %s", day, e)
        
        # 7. Calculate final score
        final_score = self._calculate_final_score(
            syntax_valid=syntax_valid,
            execution_success=execution_success,
            timeout=timeout,
            test_score=test_score,
            ai_score=ai_score,
            ai_available=ai_score is not None
        )
        
        # 8. Save review history
        self._save_review_history(day, code, ai_review)
        
        # 9. Build and save LearningRecord
        errors = self._extract_errors_from_test(test_result)
        knowledge_gaps = ai_review.get("knowledge_gaps", []) if ai_review else []
        suggestions = ai_review.get("improvement", []) if ai_review else []
        
        record = LearningRecord(
            day=day,
            task_id=str(day),
            submission_path=str(submission_path),
            test_score=test_score,
            ai_score=ai_score,
            final_score=final_score,
            errors=errors,
            knowledge_gaps=knowledge_gaps,
            suggestions=suggestions
        )
        self.database.save_submission_history(record)
        
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
    
    def _calculate_final_score(self, syntax_valid: bool, execution_success: bool,
                               timeout: bool, test_score: float, ai_score: Optional[float],
                               ai_available: bool) -> float:
        """Calculate final score
        
        Rules:
        - Syntax error or execution failure or timeout: 0 (no AI)
        - test_score < 60: final_score = test_score (no AI weighting)
        - test_score >= 60 and AI available: test_score * 0.7 + ai_score * 0.3
        - test_score >= 60 and no AI: test_score
        """
        if not syntax_valid or not execution_success or timeout:
            return 0.0
        
        if test_score < 60:
            return test_score
        
        if ai_available and ai_score is not None:
            return round(test_score * 0.7 + ai_score * 0.3, 1)
        
        return test_score
    
    def _save_review_history(self, day: int, code: str, ai_review: Optional[Dict[str, Any]]):
        """Save review history to database"""
        try:
            self.database.save_review_history(
                day=day,
                code_snippet=code[:500],
                review_result=ai_review or {}
            )
        except Exception as e:
            logger.warning("[_save_review_history] Failed to save review history: %s", e)
    
    def _get_error_history(self, current_day: int) -> List[Dict[str, Any]]:
        """获取历史错误记录"""
        history = []
        progress_list = self.database.get_all_progress()
        for p in progress_list:
            if p.day < current_day and p.ai_review:
                history.append({
                    "day": p.day,
                    "test_score": p.score,
                    "ai_score": p.ai_review.get("score"),
                    "summary": p.ai_review.get("summary", "")
                })
        return history
    
    def _extract_errors_from_test(self, test_result) -> List[Dict[str, Any]]:
        """从测试结果中提取错误信息"""
        errors = []
        for test in test_result.test_results:
            if hasattr(test, 'status') and test.status != 'passed':
                errors.append({
                    "test_name": getattr(test, 'test_name', 'unknown'),
                    "message": getattr(test, 'message', ''),
                    "error_type": self.error_classifier.classify(
                        getattr(test, 'message', '')
                    ).type
                })
        return errors
    
    def _build_student_profile(self) -> StudentProfile:
        """从数据库构建学生画像"""
        total = self.database.get_submission_count()
        avg_score = self.database.get_average_score()
        error_stats = self.database.get_error_statistics()
        
        weaknesses = self.learning_advisor.generate_advice(
            StudentProfile(error_statistics=error_stats)
        ).weaknesses
        
        return StudentProfile(
            total_submissions=total,
            average_score=avg_score,
            error_statistics=error_stats,
            weaknesses=weaknesses,
            strengths=[]
        )
    
    def get_learning_advice(self) -> Optional[Dict[str, Any]]:
        """获取学习建议"""
        profile = self._build_student_profile()
        advice = self.learning_advisor.generate_advice(profile)
        return advice.to_dict()
    
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
