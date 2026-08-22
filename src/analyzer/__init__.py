"""Error Classifier - 错误分类模块"""
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ErrorType:
    """错误类型"""
    type: str
    category: str
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type, "category": self.category, "message": self.message}


# 错误模式定义
ERROR_PATTERNS = {
    "SyntaxError": {
        "patterns": [r"SyntaxError", r"SyntaxError:"],
        "category": "Python基础"
    },
    "ImportError": {
        "patterns": [r"ImportError", r"ModuleNotFoundError", r"cannot import name"],
        "category": "Python基础"
    },
    "TensorShapeError": {
        "patterns": [
            r"mat1 and mat2 shapes cannot be multiplied",
            r"shape.*mismatch",
            r"size.*mismatch",
            r"dimension.*mismatch",
            r"Tensor.*shape",
            r"shape.*not.*match",
            r"shapes cannot be multiplied"
        ],
        "category": "PyTorch"
    },
    "RuntimeError": {
        "patterns": [r"RuntimeError", r"RuntimeError:"],
        "category": "Python运行时"
    },
    "TimeoutError": {
        "patterns": [r"TimeoutError", r"timed? ?out", r"timeout", r"DeadlineExceeded"],
        "category": "性能"
    },
    "IndexError": {
        "patterns": [r"IndexError", r"index out of range", r"list index out of range"],
        "category": "Python基础"
    },
    "KeyError": {
        "patterns": [r"KeyError", r"key.*not found"],
        "category": "Python基础"
    },
    "TypeError": {
        "patterns": [r"TypeError", r"unsupported operand", r"argument"],
        "category": "Python基础"
    },
    "ValueError": {
        "patterns": [r"ValueError", r"invalid literal", r"could not convert"],
        "category": "Python基础"
    },
    "AttributeError": {
        "patterns": [r"AttributeError", r"has no attribute"],
        "category": "Python基础"
    },
    "NameError": {
        "patterns": [r"NameError", r"name.*is not defined"],
        "category": "Python基础"
    },
    "FileNotFoundError": {
        "patterns": [r"FileNotFoundError", r"No such file or directory"],
        "category": "Python基础"
    },
}


class ErrorClassifier:
    """错误分类器

    输入: pytest错误信息
    输出: ErrorType
    """

    def classify(self, error_message: str) -> ErrorType:
        """分类错误信息

        Args:
            error_message: pytest错误信息

        Returns:
            ErrorType对象
        """
        if not error_message:
            return ErrorType(type="Unknown", category="未知", message=error_message)

        for error_type, config in ERROR_PATTERNS.items():
            for pattern in config["patterns"]:
                if re.search(pattern, error_message, re.IGNORECASE):
                    return ErrorType(
                        type=error_type,
                        category=config["category"],
                        message=error_message[:200]
                    )

        return ErrorType(type="Other", category="其他", message=error_message[:200])

    def classify_batch(self, errors: list) -> Dict[str, int]:
        """批量分类错误并统计

        Args:
            errors: 错误信息列表

        Returns:
            错误类型统计 {"TensorShapeError": 5, "ImportError": 3, ...}
        """
        stats = {}
        for error_msg in errors:
            error_type = self.classify(error_msg)
            stats[error_type.type] = stats.get(error_type.type, 0) + 1
        return stats

    def get_weaknesses(self, error_stats: Dict[str, int], threshold: int = 2) -> list:
        """根据错误统计识别薄弱点

        Args:
            error_stats: 错误统计 {"TensorShapeError": 5, ...}
            threshold: 出现次数阈值

        Returns:
            薄弱点列表
        """
        weaknesses = []
        for error_type, count in sorted(error_stats.items(), key=lambda x: -x[1]):
            if count >= threshold:
                weaknesses.append(f"{error_type} ({count}次)")
        return weaknesses
