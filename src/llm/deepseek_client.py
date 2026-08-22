"""DeepSeek LLM客户端实现"""
import os
import time
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Generator

from .base_client import BaseLLMClient, LLMResponse


class DeepSeekClient(BaseLLMClient):
    """DeepSeek API客户端
    
    支持:
    - API Key环境变量
    - 超时控制
    - 自动重试
    - 异常处理
    """
    
    def __init__(self,
                 config_path: str = "configs/config.yaml",
                 timeout: int = 30,
                 max_retries: int = 3,
                 retry_delay: float = 1.0):
        """初始化DeepSeek客户端
        
        Args:
            config_path: 配置文件路径
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试间隔（秒）
        """
        self.config = self._load_config(config_path)
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.client = None
        self.model = self.config.get("deepseek", {}).get("model", "deepseek-chat")
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
            
            api_key = self._resolve_api_key()
            if not api_key:
                print("Warning: DEEPSEEK_API_KEY not set")
                return
            
            base_url = self.config.get("deepseek", {}).get("base_url", "https://api.deepseek.com")
            
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=self.timeout
            )
            
        except ImportError:
            print("Warning: openai package not installed. Run: pip install openai")
        except Exception as e:
            print(f"Failed to initialize DeepSeek client: {e}")
    
    def _resolve_api_key(self) -> Optional[str]:
        """解析API密钥"""
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if api_key:
            return api_key
        
        deepseek_config = self.config.get("deepseek", {})
        api_key = deepseek_config.get("api_key", "")
        
        if api_key.startswith("${") and api_key.endswith("}"):
            env_var = api_key[2:-1]
            return os.getenv(env_var, "")
        
        return api_key if api_key else None
    
    def is_available(self) -> bool:
        """检查客户端是否可用"""
        return self.client is not None
    
    def chat(self,
             messages: List[Dict[str, str]],
             model: Optional[str] = None,
             temperature: float = 0.7,
             max_tokens: int = 2000) -> Optional[LLMResponse]:
        """发送聊天请求（带重试）
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            LLMResponse对象，失败返回None
        """
        if not self.client:
            return None
        
        use_model = model or self.model
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=use_model,
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
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
        
        print(f"LLM request failed after {self.max_retries} attempts: {last_error}")
        return None
    
    def chat_stream(self,
                    messages: List[Dict[str, str]],
                    model: Optional[str] = None,
                    temperature: float = 0.7,
                    max_tokens: int = 2000) -> Generator[str, None, None]:
        """流式聊天请求
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            
        Yields:
            每个token的增量内容
        """
        if not self.client:
            return
        
        use_model = model or self.model
        
        try:
            response = self.client.chat.completions.create(
                model=use_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            print(f"Stream request failed: {e}")
            return
