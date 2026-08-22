"""DeepSeek审查Agent"""
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass

from ..llm.client import LLMClient, LLMResponse


@dataclass
class ReviewResult:
    """审查结果数据类"""
    score: float
    bugs: list
    suggestions: list
    next_learning: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "bugs": self.bugs,
            "suggestions": self.suggestions,
            "next_learning": self.next_learning
        }


class DeepSeekAgent:
    """DeepSeek代码审查Agent
    
    使用DeepSeek API分析用户代码，提供反馈和建议。
    """
    
    def __init__(self, llm_client: LLMClient = None):
        """初始化DeepSeek Agent
        
        Args:
            llm_client: LLM客户端实例
        """
        self.llm_client = llm_client or LLMClient()
    
    def review_code(self, 
                   code: str, 
                   task_description: str,
                   test_results: str = "",
                   test_score: float = 0.0) -> ReviewResult:
        """审查代码
        
        Args:
            code: 用户代码
            task_description: 任务描述
            test_results: 测试结果
            test_score: 测试分数
            
        Returns:
            ReviewResult对象
        """
        if not self.llm_client.is_available():
            return self._default_review(test_score)
        
        response = self.llm_client.review_code(code, task_description, test_results)
        
        if response:
            return self._parse_review_response(response, test_score)
        
        return self._default_review(test_score)
    
    def _parse_review_response(self, response: LLMResponse, test_score: float) -> ReviewResult:
        """解析审查响应"""
        try:
            # 尝试解析JSON响应
            content = response.content
            
            # 查找JSON部分
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx]
                data = json.loads(json_str)
                
                # 计算综合分数
                ai_score = data.get("score", 70)
                # 综合分数 = 测试分数 * 50% + AI评分 * 50%
                final_score = test_score * 0.5 + ai_score * 0.5
                
                return ReviewResult(
                    score=final_score,
                    bugs=data.get("bugs", []),
                    suggestions=data.get("suggestions", []),
                    next_learning=data.get("next_learning", "")
                )
            
            # 如果没有找到JSON，使用默认解析
            return self._default_review(test_score)
            
        except json.JSONDecodeError:
            return self._default_review(test_score)
    
    def _default_review(self, test_score: float) -> ReviewResult:
        """默认审查结果"""
        return ReviewResult(
            score=test_score,
            bugs=[],
            suggestions=["代码需要进一步优化"],
            next_learning=""
        )
    
    def analyze_learning_path(self, 
                             history: list, 
                             current_day: int) -> Dict[str, Any]:
        """分析学习路径
        
        Args:
            history: 学习历史
            current_day: 当前天数
            
        Returns:
            分析结果
        """
        if not self.llm_client.is_available():
            return {
                "weak_points": [],
                "recommendations": [],
                "difficulty_adjustment": "normal"
            }
        
        # 构建提示
        system_prompt = """你是一个AI学习导师。请分析学生的学习历史，识别薄弱知识点，并提供个性化学习建议。

请提供：
1. 薄弱知识点列表
2. 推荐复习内容
3. 难度调整建议（easy/normal/hard）
4. 下一步学习建议"""
        
        user_prompt = f"""学生学习历史：
{json.dumps(history, ensure_ascii=False, indent=2)}

当前进度：第{current_day}天

请分析学生的学习情况。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.llm_client.chat(messages, temperature=0.5)
        
        if response:
            try:
                content = response.content
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                
                if start_idx != -1 and end_idx != -1:
                    json_str = content[start_idx:end_idx]
                    return json.loads(json_str)
            except:
                pass
        
        return {
            "weak_points": [],
            "recommendations": [],
            "difficulty_adjustment": "normal"
        }
    
    def generate_feedback(self, 
                         code: str, 
                         score: float,
                         test_passed: bool) -> str:
        """生成反馈消息
        
        Args:
            code: 用户代码
            score: 分数
            test_passed: 测试是否通过
            
        Returns:
            反馈消息
        """
        if score >= 90:
            return "优秀！你的代码质量很高，继续保持！"
        elif score >= 70:
            return "良好！代码功能正确，可以进一步优化代码质量。"
        elif score >= 60:
            return "及格。代码基本功能实现，建议查看测试失败的原因。"
        else:
            return "需要改进。请仔细查看测试结果和错误信息。"
    
    def get_next_task_suggestion(self, 
                                current_day: int, 
                                current_score: float) -> str:
        """获取下一个任务建议
        
        Args:
            current_day: 当前天数
            current_score: 当前分数
            
        Returns:
            建议消息
        """
        if current_score >= 90:
            return f"太棒了！准备好挑战第{current_day + 1}天的任务了吗？"
        elif current_score >= 70:
            return f"不错！可以尝试第{current_day + 1}天的任务，但建议先复习一下薄弱环节。"
        elif current_score >= 60:
            return f"建议先巩固第{current_day}天的内容，然后再继续。"
        else:
            return f"建议重新学习第{current_day}天的内容，确保基础扎实。"