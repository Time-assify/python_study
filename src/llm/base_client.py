"""LLM统一接口层 - 抽象基类"""
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Generator
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """LLM响应数据类"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str


class BaseLLMClient(ABC):
    """LLM客户端抽象基类
    
    所有LLM调用必须经过此接口。
    """
    
    @abstractmethod
    def chat(self,
             messages: List[Dict[str, str]],
             model: Optional[str] = None,
             temperature: float = 0.7,
             max_tokens: int = 2000) -> Optional[LLMResponse]:
        """发送聊天请求
        
        Args:
            messages: 消息列表 [{"role": "system/user/assistant", "content": "..."}]
            model: 模型名称（None则使用默认）
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            LLMResponse对象，失败返回None
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查客户端是否可用"""
        pass
    
    def _extract_json(self, content: str) -> Optional[Dict[str, Any]]:
        """从LLM响应中提取JSON
        
        Args:
            content: LLM响应内容
            
        Returns:
            解析后的字典，失败返回None
        """
        try:
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass
        return None
