"""Code Review Agent - AI代码审查模块"""
import json
import traceback
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from ..llm.base_client import BaseLLMClient
from ..models import StudentProfile, ReviewResult

CodeReviewResult = ReviewResult


class CodeReviewAgent:
    """Code Review Agent

    使用LLM分析学生代码，提供专业的学习反馈。
    不参与功能正确性判断，只关注代码质量和学习指导。
    """

    SYSTEM_PROMPT = """你是一名资深的Python和PyTorch学习导师。你的职责是帮助学生提高编程能力。

## 核心教学原则
1. **引导思考** - 不要直接给答案，引导学生自己发现问题
2. **解释Why** - 解释每个问题背后的原因，让学生知其然更知其所以然
3. **关联知识** - 将代码问题与相关知识点联系起来
4. **鼓励进步** - 指出问题的同时肯定进步，保持学习动力
5. **循序渐进** - 根据学生当前水平给出合适难度的建议

## 审查维度
你需要从以下6个维度分析学生代码：

1. **代码结构** - 命名是否清晰，模块划分是否合理
2. **Python/PyTorch规范** - 是否遵循PEP8，是否有Pythonic写法
3. **可读性** - 代码是否易于理解
4. **性能** - 是否有明显性能问题
5. **潜在工程问题** - 是否有隐藏的bug或不安全操作
6. **知识漏洞** - 学生对哪些概念理解不足

## 重要说明
- pytest测试结果已经确定了功能正确性，你**不需要**判断代码功能是否正确
- 你只负责评估代码质量和给出学习建议
- 功能正确性由pytest结果决定，不要重新判断

## 输出要求
你必须返回严格的JSON格式，不要包含任何其他文本：

{
  "score": 85,
  "summary": "整体评价（1-2句话）",
  "strengths": ["优点1", "优点2"],
  "issues": ["问题1（附带原因）", "问题2"],
  "knowledge_gaps": ["概念1需要加强", "概念2理解不深"],
  "improvement": ["改进建议1（具体方法）", "改进建议2"],
  "next_learning": ["下一步应该学习的内容1", "内容2"]
}

## 评分标准
- 90-100: 优秀 - 代码清晰、规范、高效
- 75-89: 良好 - 功能正确，有改进空间
- 60-74: 及格 - 基本功能实现，需要优化
- 0-59: 需要改进 - 存在明显问题"""

    def __init__(self, llm_client: BaseLLMClient):
        """初始化Code Review Agent

        Args:
            llm_client: LLM客户端实例（必须实现BaseLLMClient接口）
        """
        self.llm_client = llm_client

    def review(self,
               day: int,
               code: str,
               task: Dict[str, Any],
               requirement: str,
               pytest_result: Dict[str, Any],
               history: Optional[List[Dict[str, Any]]] = None,
               profile: Optional[StudentProfile] = None) -> CodeReviewResult:
        """执行代码审查

        Args:
            day: 当前天数
            code: 学生提交的代码
            task: 当天任务描述 {"title": "...", "description": "...", "goal": "..."}
            requirement: 任务的具体要求（来自task.json）
            pytest_result: pytest测试结果 {"total": N, "passed": N, "failed": N, "errors": N, "details": [...]}
            history: 历史错误记录（可选）
            profile: 学生画像（可选，用于个性化反馈）

        Returns:
            CodeReviewResult对象
        """
        if not self.llm_client.is_available():
            return self._default_result(day=day)

        try:
            user_prompt = self._build_prompt(day, code, task, requirement, pytest_result, history, profile)

            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]

            response = self.llm_client.chat(messages, temperature=0.3, max_tokens=2000)

            if response is None:
                print(f"[CodeReviewAgent] LLM返回None，使用默认结果")
                return self._default_result(day=day)

            result = self._parse_response(response.content)
            # P0-3: 非法schema不得被标记为success参与评分
            if result.review_status == "invalid_response":
                result.day = day
                return result
            result.day = day
            result.review_status = "success"
            return result

        except Exception as e:
            print(f"[CodeReviewAgent] 审查出错: {e}")
            traceback.print_exc()
            return self._default_result(day=day, review_status="error")

    def _build_prompt(self,
                      day: int,
                      code: str,
                      task: Dict[str, Any],
                      requirement: str,
                      pytest_result: Dict[str, Any],
                      history: Optional[List[Dict[str, Any]]],
                      profile: Optional[StudentProfile]) -> str:
        """构建审查提示

        Args:
            day: 当前天数
            code: 学生代码
            task: 任务信息
            requirement: 具体要求
            pytest_result: 测试结果
            history: 历史记录
            profile: 学生画像

        Returns:
            完整的用户提示
        """
        prompt = f"""请审查第{day}天学生提交的代码：

## 任务信息
- 标题: {task.get('title', '未知任务')}
- 描述: {task.get('description', '无描述')}
- 目标: {task.get('goal', '无目标')}

## 具体要求
{requirement}

## 测试结果
- 总测试数: {pytest_result.get('total', 0)}
- 通过: {pytest_result.get('passed', 0)}
- 失败: {pytest_result.get('failed', 0)}
- 错误: {pytest_result.get('errors', 0)}"""

        details = pytest_result.get('details', [])
        failed_tests = [d for d in details if d.get('status') != 'passed']
        if failed_tests:
            prompt += "\n\n### 失败/错误详情"
            for i, test in enumerate(failed_tests[:5], 1):
                prompt += f"\n{i}. {test.get('test_name', 'unknown')}: {test.get('message', '')[:200]}"

        if history:
            # P0-4: history约定为 newest-first，取最近5条
            prompt += "\n\n### 历史错误记录（最近的在前）"
            for h in history[:5]:
                prompt += f"\n- Day {h.get('day', '?')}: {h.get('error_type', 'unknown')}: {str(h.get('message', ''))[:100]}"

        if profile:
            prompt += "\n\n### 学生画像"
            prompt += f"\n- 总提交次数: {profile.total_submissions}"
            prompt += f"\n- 平均分: {profile.average_score}"
            if profile.error_statistics:
                prompt += "\n- 错误统计:"
                for error_type, count in sorted(profile.error_statistics.items(), key=lambda x: -x[1]):
                    prompt += f"\n  - {error_type}: {count}次"
            if profile.weaknesses:
                prompt += "\n- 薄弱点: " + "、".join(profile.weaknesses[:3])
            if profile.strengths:
                prompt += "\n- 优点: " + "、".join(profile.strengths[:3])

        prompt += f"""

## 学生代码
```python
{code}
```

请从代码结构、Python/PyTorch规范、可读性、性能、潜在工程问题、知识漏洞6个维度进行审查，并给出改进建议。"""

        return prompt

    def _parse_response(self, content: str) -> CodeReviewResult:
        """解析LLM响应（P0-3: 严格schema校验，非法即降级）

        - score: 数字且 0 <= score <= 100
        - strengths/issues/knowledge_gaps/improvement/next_learning:
          必须是 list[str]（拒绝字符串/含非字符串元素的list）
        - summary: 必须是str

        任一字段非法 → _default_result(review_status="invalid_response")，
        不让invalid AI响应参与最终评分。
        """
        try:
            data = self.llm_client._extract_json(content)
        except (ValueError, TypeError):
            data = None

        if not self._validate_schema(data):
            return self._default_result(review_status="invalid_response")

        return CodeReviewResult(
            score=float(data["score"]),
            summary=str(data["summary"]),
            strengths=[str(s) for s in data["strengths"]],
            issues=[str(i) for i in data["issues"]],
            knowledge_gaps=[str(g) for g in data["knowledge_gaps"]],
            improvement=[str(m) for m in data["improvement"]],
            next_learning=[str(n) for n in data["next_learning"]],
        )

    @staticmethod
    def _validate_schema(data) -> bool:
        """结构化输出schema校验"""
        if not isinstance(data, dict):
            return False

        score = data.get("score")
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            return False
        if not (0 <= score <= 100):
            return False

        if not isinstance(data.get("summary"), str):
            return False

        list_fields = ("strengths", "issues", "knowledge_gaps",
                       "improvement", "next_learning")
        for field in list_fields:
            value = data.get(field)
            if not isinstance(value, list):
                return False
            if not all(isinstance(v, str) for v in value):
                return False
        return True

    def _default_result(self, day: int = 0, review_status: str = "fallback") -> CodeReviewResult:
        """返回默认审查结果（LLM不可用时）"""
        return CodeReviewResult(
            day=day,
            score=None,
            summary="AI审查不可用，无法进行代码分析",
            strengths=[],
            issues=["无法获取AI审查结果"],
            knowledge_gaps=[],
            improvement=["请确保DEEPSEEK_API_KEY环境变量已设置"],
            next_learning=[],
            review_status=review_status
        )
