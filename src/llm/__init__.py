"""LLM统一接口层"""
from .base_client import BaseLLMClient, LLMResponse
from .deepseek_client import DeepSeekClient

# 向后兼容：LLMClient = DeepSeekClient
LLMClient = DeepSeekClient

__all__ = ["BaseLLMClient", "LLMResponse", "DeepSeekClient", "LLMClient"]
