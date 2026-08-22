"""Learning Advisor - 学习建议生成模块"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from ..models import StudentProfile


# 知识点与学习建议映射
KNOWLEDGE_ADVICE = {
    "PyTorch Tensor维度": {
        "related": ["TensorShapeError", "维度不匹配", "shape"],
        "advice": [
            "建议重新学习：PyTorch Tensor维度",
            "增加：CNN shape练习",
            "复习 torch.view() 和 torch.reshape() 用法",
            "练习：print(tensor.shape) 观察维度变化"
        ]
    },
    "Python基础语法": {
        "related": ["SyntaxError", "语法错误"],
        "advice": [
            "建议重新学习：Python基础语法",
            "复习缩进、括号、冒号规则",
            "使用IDE的语法检查功能"
        ]
    },
    "模块导入": {
        "related": ["ImportError", "ModuleNotFoundError"],
        "advice": [
            "建议重新学习：Python模块导入",
            "检查pip install是否安装",
            "确认导入路径是否正确",
            "复习 from ... import ... 和 import ... 的区别"
        ]
    },
    "PyTorch模型定义": {
        "related": ["模型错误", "nn.Module"],
        "advice": [
            "建议重新学习：PyTorch nn.Module",
            "复习 __init__ 和 forward 方法",
            "练习：手写一个简单的Linear模型"
        ]
    },
    "训练循环": {
        "related": ["训练错误", "loss", "optimizer"],
        "advice": [
            "建议重新学习：训练循环流程",
            "复习：zero_grad → forward → loss → backward → step",
            "练习：手写完整训练循环"
        ]
    },
    "数据加载": {
        "related": ["DataLoader", "Dataset", "数据错误"],
        "advice": [
            "建议重新学习：PyTorch数据加载",
            "复习 Dataset 和 DataLoader 的关系",
            "练习：自定义Dataset类"
        ]
    },
}


@dataclass
class LearningAdvice:
    """学习建议"""
    weaknesses: List[str]
    suggestions: List[str]
    priority_topics: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LearningAdvisor:
    """学习建议生成器

    根据学生画像生成下一步学习建议。
    """

    def __init__(self):
        pass

    def generate_advice(self, profile: StudentProfile) -> LearningAdvice:
        """根据学生画像生成学习建议

        Args:
            profile: 学生画像

        Returns:
            LearningAdvice对象
        """
        weaknesses = []
        suggestions = []
        priority_topics = []

        error_stats = profile.error_statistics or {}

        if not error_stats:
            return LearningAdvice(
                weaknesses=[],
                suggestions=["暂无历史数据，请先完成几次练习"],
                priority_topics=[]
            )

        for error_type, count in sorted(error_stats.items(), key=lambda x: -x[1]):
            weaknesses.append(f"{error_type} ({count}次)")

            matched = False
            for topic, config in KNOWLEDGE_ADVICE.items():
                if error_type in config["related"] or any(r in error_type for r in config["related"]):
                    suggestions.extend(config["advice"])
                    priority_topics.append(topic)
                    matched = True
                    break

            if not matched:
                suggestions.append(f"建议复习：{error_type}相关知识")

        return LearningAdvice(
            weaknesses=list(set(weaknesses)),
            suggestions=list(set(suggestions)),
            priority_topics=list(set(priority_topics))
        )

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
