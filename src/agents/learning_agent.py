"""学习Agent模块"""
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..llm.client import LLMClient


@dataclass
class LearningRecommendation:
    """学习推荐数据类"""
    weak_points: List[str]
    recommended_review: List[str]
    difficulty_adjustment: str  # easy, normal, hard
    next_tasks: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "weak_points": self.weak_points,
            "recommended_review": self.recommended_review,
            "difficulty_adjustment": self.difficulty_adjustment,
            "next_tasks": self.next_tasks
        }


class LearningAgent:
    """学习分析Agent
    
    分析用户学习历史，提供个性化学习建议。
    """
    
    def __init__(self, llm_client: LLMClient = None):
        """初始化学习Agent
        
        Args:
            llm_client: LLM客户端实例
        """
        self.llm_client = llm_client or LLMClient()
    
    def analyze_performance(self, 
                          progress_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析学习表现
        
        Args:
            progress_history: 学习进度历史
            
        Returns:
            分析结果
        """
        if not progress_history:
            return self._empty_analysis()
        
        # 计算基本统计
        scores = [p.get("score", 0) for p in progress_history]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # 分析趋势
        trend = self._analyze_trend(scores)
        
        # 识别薄弱环节
        weak_points = self._identify_weak_points(progress_history)
        
        return {
            "average_score": round(avg_score, 2),
            "trend": trend,
            "weak_points": weak_points,
            "completion_rate": len(progress_history) / 40 * 100,
            "total_submissions": sum(p.get("submissions", 0) for p in progress_history)
        }
    
    def _analyze_trend(self, scores: List[float]) -> str:
        """分析分数趋势"""
        if len(scores) < 2:
            return "insufficient_data"
        
        # 计算最近几次的平均分
        recent_avg = sum(scores[-3:]) / min(3, len(scores))
        earlier_avg = sum(scores[:-3]) / max(1, len(scores) - 3)
        
        if recent_avg > earlier_avg + 5:
            return "improving"
        elif recent_avg < earlier_avg - 5:
            return "declining"
        else:
            return "stable"
    
    def _identify_weak_points(self, progress_history: List[Dict[str, Any]]) -> List[str]:
        """识别薄弱知识点"""
        weak_points = []
        
        # 找出得分低的任务
        for progress in progress_history:
            score = progress.get("score", 0)
            day = progress.get("day", 0)
            
            if score < 60:
                weak_points.append(f"Day {day}: 基础知识薄弱")
            elif score < 70:
                weak_points.append(f"Day {day}: 需要加强练习")
        
        return weak_points[:5]  # 最多返回5个
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """空分析结果"""
        return {
            "average_score": 0,
            "trend": "no_data",
            "weak_points": [],
            "completion_rate": 0,
            "total_submissions": 0
        }
    
    def get_learning_recommendation(self, 
                                   current_day: int,
                                   progress_history: List[Dict[str, Any]]) -> LearningRecommendation:
        """获取学习推荐
        
        Args:
            current_day: 当前天数
            progress_history: 学习进度历史
            
        Returns:
            LearningRecommendation对象
        """
        # 分析当前表现
        analysis = self.analyze_performance(progress_history)
        
        # 根据分析结果生成推荐
        weak_points = analysis.get("weak_points", [])
        avg_score = analysis.get("average_score", 0)
        
        # 确定难度调整
        if avg_score >= 80:
            difficulty = "hard"
        elif avg_score >= 60:
            difficulty = "normal"
        else:
            difficulty = "easy"
        
        # 生成推荐复习内容
        recommended_review = self._get_review_recommendations(weak_points, current_day)
        
        # 推荐下一个任务
        next_tasks = self._recommend_next_tasks(current_day, avg_score)
        
        return LearningRecommendation(
            weak_points=weak_points,
            recommended_review=recommended_review,
            difficulty_adjustment=difficulty,
            next_tasks=next_tasks
        )
    
    def _get_review_recommendations(self, weak_points: List[str], current_day: int) -> List[str]:
        """获取复习推荐"""
        recommendations = []
        
        # 根据薄弱点推荐复习
        for weak_point in weak_points[:3]:
            if "Day" in weak_point:
                day_num = int(weak_point.split()[1])
                recommendations.append(f"复习Day {day_num}的内容")
        
        # 添加通用推荐
        if not recommendations:
            recommendations.append("巩固基础Python知识")
        
        return recommendations
    
    def _recommend_next_tasks(self, current_day: int, avg_score: float) -> List[str]:
        """推荐下一个任务"""
        tasks = []
        
        if avg_score >= 70:
            tasks.append(f"继续Day {current_day + 1}的学习")
            if current_day + 1 <= 40:
                tasks.append(f"挑战Day {current_day + 1}的进阶内容")
        else:
            tasks.append(f"巩固Day {current_day}的内容")
            tasks.append("完成所有练习题")
        
        return tasks
    
    def generate_study_plan(self, 
                          current_day: int,
                          available_hours: float,
                          progress_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成学习计划
        
        Args:
            current_day: 当前天数
            available_hours: 可用学习时间（小时）
            progress_history: 学习进度历史
            
        Returns:
            学习计划
        """
        analysis = self.analyze_performance(progress_history)
        avg_score = analysis.get("average_score", 0)
        
        # 根据可用时间和当前水平分配时间
        if avg_score >= 80:
            # 高水平：更多时间用于实践
            theory_time = available_hours * 0.3
            practice_time = available_hours * 0.5
            review_time = available_hours * 0.2
        elif avg_score >= 60:
            # 中等水平：平衡分配
            theory_time = available_hours * 0.4
            practice_time = available_hours * 0.4
            review_time = available_hours * 0.2
        else:
            # 初学者：更多时间用于理论
            theory_time = available_hours * 0.5
            practice_time = available_hours * 0.3
            review_time = available_hours * 0.2
        
        return {
            "current_day": current_day,
            "total_hours": available_hours,
            "plan": {
                "theory": round(theory_time, 1),
                "practice": round(practice_time, 1),
                "review": round(review_time, 1)
            },
            "focus_areas": analysis.get("weak_points", [])[:2],
            "goals": [
                f"完成Day {current_day}的任务",
                "理解核心概念",
                "完成所有练习"
            ]
        }
    
    def track_progress(self, 
                      day: int, 
                      score: float, 
                      test_results: Dict) -> Dict[str, Any]:
        """跟踪学习进度
        
        Args:
            day: 天数
            score: 分数
            test_results: 测试结果
            
        Returns:
            进度跟踪信息
        """
        # 分析测试结果
        passed_tests = sum(1 for r in test_results.values() if r.get("passed", False))
        total_tests = len(test_results)
        
        # 生成进度报告
        progress = {
            "day": day,
            "score": score,
            "tests_passed": passed_tests,
            "tests_total": total_tests,
            "pass_rate": round(passed_tests / max(total_tests, 1) * 100, 1),
            "status": "completed" if score >= 60 else "needs_improvement"
        }
        
        # 添加建议
        if score < 60:
            progress["suggestion"] = "建议重新学习本章内容"
        elif score < 80:
            progress["suggestion"] = "可以继续，但建议加强练习"
        else:
            progress["suggestion"] = "表现优秀，可以挑战更高难度"
        
        return progress