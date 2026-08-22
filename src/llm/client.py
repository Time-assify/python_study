"""LLM客户端模块"""
import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """LLM响应数据类"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str


class LLMClient:
    """LLM客户端
    
    封装DeepSeek API调用，使用OpenAI兼容SDK。
    """
    
    def __init__(self, config_path: str = "configs/config.yaml"):
        """初始化LLM客户端
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.client = None
        self._init_client()
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def _init_client(self):
        """初始化OpenAI客户端"""
        try:
            from openai import OpenAI
            
            # 获取API密钥
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                # 尝试从配置文件获取
                deepseek_config = self.config.get("deepseek", {})
                api_key = deepseek_config.get("api_key", "")
                
                # 如果是环境变量引用
                if api_key.startswith("${") and api_key.endswith("}"):
                    env_var = api_key[2:-1]
                    api_key = os.getenv(env_var, "")
            
            if not api_key:
                print("警告: 未设置DEEPSEEK_API_KEY环境变量")
                return
            
            # 获取base_url
            base_url = "https://api.deepseek.com"
            
            # 初始化客户端
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            
        except ImportError:
            print("警告: 未安装openai库，请运行: pip install openai")
        except Exception as e:
            print(f"初始化LLM客户端失败: {e}")
    
    def is_available(self) -> bool:
        """检查客户端是否可用"""
        return self.client is not None
    
    def chat(self, 
             messages: List[Dict[str, str]], 
             model: str = None,
             temperature: float = 0.7,
             max_tokens: int = 2000) -> Optional[LLMResponse]:
        """发送聊天请求
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            LLMResponse对象
        """
        if not self.client:
            print("LLM客户端未初始化")
            return None
        
        if model is None:
            model = self.config.get("deepseek", {}).get("model", "deepseek-chat")
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            choice = response.choices[0]
            return LLMResponse(
                content=choice.message.content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                finish_reason=choice.finish_reason
            )
            
        except Exception as e:
            print(f"LLM请求失败: {e}")
            return None
    
    def review_code(self, 
                   code: str, 
                   task_description: str,
                   test_results: str = "") -> Optional[LLMResponse]:
        """代码审查
        
        Args:
            code: 用户代码
            task_description: 任务描述
            test_results: 测试结果
            
        Returns:
            LLMResponse对象
        """
        system_prompt = """你是一个专业的代码审查助手。请分析用户提交的代码，并提供以下信息：
1. 代码质量评分（0-100分）
2. 发现的bug列表
3. 改进建议
4. 下一步学习建议

请以JSON格式返回结果：
{
  "score": 90,
  "bugs": ["bug1", "bug2"],
  "suggestions": ["建议1", "建议2"],
  "next_learning": "建议学习的内容"
}"""
        
        user_prompt = f"""请审查以下代码：

任务描述：
{task_description}

用户代码：
```python
{code}
```

测试结果：
{test_results}

请提供详细的代码审查报告。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.chat(messages, temperature=0.3)
    
    def analyze_learning(self, 
                        history: List[Dict[str, Any]],
                        current_task: str) -> Optional[LLMResponse]:
        """分析学习情况
        
        Args:
            history: 学习历史
            current_task: 当前任务
            
        Returns:
            LLMResponse对象
        """
        system_prompt = """你是一个AI学习导师。请根据学生的学习历史，分析其薄弱知识点，并提供个性化的学习建议。

请提供：
1. 薄弱知识点列表
2. 推荐复习内容
3. 下一任务难度建议
4. 学习路径调整建议"""
        
        user_prompt = f"""学生学习历史：
{history}

当前任务：{current_task}

请分析学生的学习情况并提供个性化建议。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.chat(messages, temperature=0.5)
    
    def generate_report(self, 
                       progress_data: Dict[str, Any],
                       statistics: Dict[str, Any]) -> Optional[LLMResponse]:
        """生成学习报告
        
        Args:
            progress_data: 进度数据
            statistics: 统计信息
            
        Returns:
            LLMResponse对象
        """
        system_prompt = """你是一个学习报告生成助手。请根据学生的学习数据生成一份详细的学习报告。

报告应包括：
1. 学习进度概述
2. 成绩分析
3. 优势和不足
4. 改进建议
5. 下一步计划

请使用Markdown格式生成报告。"""
        
        user_prompt = f"""学习进度数据：
{progress_data}

统计信息：
{statistics}

请生成一份详细的学习报告。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.chat(messages, temperature=0.5)
    
    def explain_concept(self, concept: str, level: str = "beginner") -> Optional[LLMResponse]:
        """解释概念
        
        Args:
            concept: 概念名称
            level: 理解水平（beginner/intermediate/advanced）
            
        Returns:
            LLMResponse对象
        """
        system_prompt = f"""你是一个技术概念解释助手。请用{level}水平解释以下概念。

解释要求：
1. 使用简单易懂的语言
2. 提供实际例子
3. 解释为什么重要
4. 提供学习资源链接"""
        
        user_prompt = f"请解释概念：{concept}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.chat(messages, temperature=0.5)