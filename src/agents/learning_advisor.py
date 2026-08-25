"""Learning Advisor - 学习建议生成模块

P1-1: 综合使用StudentProfile的完整字段：
- error_statistics（客观错误，来自ErrorClassifier）
- knowledge_gap_statistics（AI判断的知识漏洞）
- trend（improving/stable/declining）
- strengths
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from ..models import StudentProfile


# 客观错误类型 -> 知识点映射
ERROR_TOPIC_MAP = {
    "TensorShapeError": {
        "topic": "PyTorch Tensor维度",
        "advice": [
            "优先复习：PyTorch Tensor shape与Conv2d尺寸计算",
            "练习：print(tensor.shape)观察每层维度变化",
            "复习 torch.view() 和 torch.reshape() 用法"
        ]
    },
    "SyntaxError": {
        "topic": "Python基础语法",
        "advice": [
            "建议重新学习：Python基础语法",
            "复习缩进、括号、冒号规则"
        ]
    },
    "ImportError": {
        "topic": "模块导入",
        "advice": [
            "建议重新学习：Python模块导入",
            "确认依赖已安装、导入路径正确"
        ]
    },
    "LogicError": {
        "topic": "逻辑与边界条件",
        "advice": [
            "建议练习：边界条件分析（空输入/极值）",
            "用print或断言验证中间变量"
        ]
    },
    "RuntimeError": {
        "topic": "运行时错误排查",
        "advice": [
            "建议学习：阅读traceback定位错误根因"
        ]
    },
    "TimeoutError": {
        "topic": "性能优化",
        "advice": [
            "建议学习：算法复杂度与向量化操作"
        ]
    },
}

# AI知识漏洞关键词 -> 知识点映射
GAP_TOPIC_MAP = {
    "tensor": {"topic": "PyTorch Tensor维度", "advice": ["增加：CNN shape练习"]},
    "维度": {"topic": "PyTorch Tensor维度", "advice": ["增加：CNN shape练习"]},
    "shape": {"topic": "PyTorch Tensor维度", "advice": ["增加：CNN shape练习"]},
    "训练循环": {"topic": "训练循环流程", "advice": ["复习：zero_grad → forward → loss → backward → step"]},
    "loss": {"topic": "损失函数", "advice": ["复习常见loss的输入输出shape约定"]},
    "导入": {"topic": "模块导入", "advice": ["复习 from ... import ... 与 import ... 的区别"]},
    "数据加载": {"topic": "Dataset/DataLoader", "advice": ["练习：自定义Dataset类"]},
}


@dataclass
class LearningAdvice:
    """学习建议"""
    weaknesses: List[str]
    suggestions: List[str]
    priority_topics: List[str]
    trend_note: str = ""
    difficulty_recommendation: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LearningAdvisor:
    """学习建议生成器
    
    根据学生画像（错误统计+知识漏洞+趋势+优点）生成下一步学习建议。
    """

    def __init__(self):
        pass

    def generate_advice(self, profile: StudentProfile,
                        recent_results: Optional[List[Dict[str, Any]]] = None,
                        current_difficulty: Optional[int] = None) -> LearningAdvice:
        """综合学生画像生成学习建议

        Args:
                profile: 学生画像（含error_statistics/knowledge_gap_statistics/trend/strengths）
            recent_results: 最近提交（newest-first）[{passed: bool, difficulty: int}, ...]
                            提供时启用P0-2难度推荐规则
            current_difficulty: 当前任务难度(1-5)

        Returns:
            LearningAdvice对象
        """
        error_stats = profile.error_statistics or {}
        gap_stats = profile.knowledge_gap_statistics or {}
        
        weaknesses = list(profile.weaknesses or [])
        suggestions = []
        priority_topics = []
        
        # 1. 基于客观错误生成建议
        for error_type, count in sorted(error_stats.items(), key=lambda x: -x[1]):
            if count >= 2:
                weaknesses.append(f"{error_type} ({count}次)")
            config = ERROR_TOPIC_MAP.get(error_type)
            if config:
                suggestions.extend(config["advice"])
                priority_topics.append(config["topic"])
            else:
                suggestions.append(f"建议复习：{error_type}相关知识")
        
        # 2. 基于AI判断的知识漏洞生成建议（与客观错误交叉验证）
        for gap, count in sorted(gap_stats.items(), key=lambda x: -x[1]):
            matched = False
            for keyword, config in GAP_TOPIC_MAP.items():
                if keyword in gap:
                    if config["topic"] not in priority_topics:
                        priority_topics.append(config["topic"])
                    suggestions.extend(config["advice"])
                    matched = True
                    break
            if not matched and count >= 2:
                weaknesses.append(f"{gap} ({count}次)")
                suggestions.append(f"针对性练习：{gap}")
        
        # 3. 基于trend给出节奏建议
        trend_note = ""
        if profile.trend == "declining":
            trend_note = "近期成绩下降，建议降低下一任务难度并安排复习"
            suggestions.insert(0, trend_note)
        elif profile.trend == "improving":
            trend_note = "近期成绩持续提升，可以按计划继续推进"
        
        # 4. 基于strengths给予正向反馈
        if profile.strengths:
            top_strength = profile.strengths[0]
            suggestions.append(f"继续保持优点：{top_strength}")

        # 5. P0-2: 基于最近通过/失败连击的难度推荐（简单规则）
        difficulty_recommendation = None
        if recent_results:
            difficulty_recommendation = self.recommend_difficulty(
                recent_results, current_difficulty
            )
            if difficulty_recommendation.get("reason"):
                suggestions.insert(0, difficulty_recommendation["reason"])

        # 无任何数据时的默认建议
        if not error_stats and not gap_stats and not recent_results:
            return LearningAdvice(
                weaknesses=[],
                suggestions=["暂无历史数据，请先完成几次练习"],
                priority_topics=[],
                trend_note=trend_note,
                difficulty_recommendation=None
            )
        
        # 去重保序
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            if s not in seen:
                seen.add(s)
                unique_suggestions.append(s)
        unique_topics = []
        for t in priority_topics:
            if t not in unique_topics:
                unique_topics.append(t)
        
        return LearningAdvice(
            weaknesses=list(dict.fromkeys(weaknesses)),
            suggestions=unique_suggestions,
            priority_topics=unique_topics,
            trend_note=trend_note,
            difficulty_recommendation=difficulty_recommendation
        )

    @staticmethod
    def recommend_difficulty(recent_results: List[Dict[str, Any]],
                             current_difficulty: Optional[int] = None) -> Dict[str, Any]:
        """P0-2: 基于最近连击的难度推荐（简单规则，不做复杂算法）

        规则:
        - 最近连续失败>=2 → 下一任务难度 <= 当前失败任务的difficulty
        - 最近连续通过>=3 → 允许difficulty+1
        - 其他 → 维持当前难度

        Args:
            recent_results: newest-first列表 [{passed: bool, difficulty: int}, ...]
            current_difficulty: 当前任务难度

        Returns:
            {mode, max_difficulty, reason}
        """
        cur = current_difficulty if isinstance(current_difficulty, int) else 3

        fail_streak = 0
        for r in recent_results:
            if r.get("passed"):
                break
            fail_streak += 1

        pass_streak = 0
        for r in recent_results:
            if not r.get("passed"):
                break
            pass_streak += 1

        if fail_streak >= 2:
            failing_difficulty = next(
                (r["difficulty"] for r in recent_results[:fail_streak]
                 if isinstance(r.get("difficulty"), int)),
                cur
            )
            cap = min(cur if isinstance(current_difficulty, int) else failing_difficulty,
                      failing_difficulty)
            return {
                "mode": "reduce",
                "max_difficulty": max(1, cap),
                "reason": f"连续失败{fail_streak}次，建议选择难度不超过{max(1, cap)}的任务巩固基础"
            }
        if pass_streak >= 3:
            target = min(5, (cur if isinstance(current_difficulty, int) else 3) + 1)
            return {
                "mode": "advance",
                "max_difficulty": target,
                "reason": f"连续通过{pass_streak}次，可以挑战难度{target}的任务"
            }
        return {
            "mode": "maintain",
            "max_difficulty": cur,
            "reason": f"保持当前难度{cur}继续练习"
        }

    def get_priority_score(self, error_type: str, count: int) -> int:
        """计算错误类型的优先级分数

        Args:
            error_type: 错误类型
            count: 出现次数

        Returns:
            优先级分数 (越高越优先)
        """
        base_score = count * 10
        penalty_map = {
            "TensorShapeError": 5,
            "ImportError": 3,
            "SyntaxError": 2,
        }
        penalty = penalty_map.get(error_type, 0)
        return base_score + penalty
