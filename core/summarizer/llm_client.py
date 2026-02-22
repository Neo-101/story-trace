from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from openai import OpenAI, AsyncOpenAI
import asyncio

class LLMClient(ABC):
    """LLM 客户端抽象基类"""
    @abstractmethod
    def chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        pass

    @abstractmethod
    async def chat_completion_async(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """异步调用接口"""
        pass

class OpenAIClient(LLMClient):
    """基于 OpenAI SDK 的通用客户端 (支持 OpenRouter, Local, DeepSeek 等)"""
    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.async_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM 同步调用失败: {e}")
            raise e

    def generate(self, prompt: str) -> str:
        """Alias for chat_completion with a single user message (for compatibility)"""
        return self.chat_completion([{"role": "user", "content": prompt}])

    async def chat_completion_async(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM 异步调用失败: {e}")
            raise e

class ClientFactory:
    """工厂类，用于创建不同类型的 LLM 客户端"""
    @staticmethod
    def create_client(provider: str, **kwargs) -> LLMClient:
        if provider == "local":
            return OpenAIClient(
                api_key="lm-studio", # 本地通常不需要真实 Key
                base_url=kwargs.get("base_url", "http://localhost:1234/v1"),
                model=kwargs.get("model", "local-model")
            )
        elif provider == "openrouter":
            return OpenAIClient(
                api_key=kwargs.get("api_key"),
                base_url="https://openrouter.ai/api/v1",
                model=kwargs.get("model", "openai/gpt-3.5-turbo")
            )
        elif provider == "deepseek":
            return OpenAIClient(
                api_key=kwargs.get("api_key"),
                base_url="https://api.deepseek.com",
                model=kwargs.get("model", "deepseek-chat")
            )
        else:
            raise ValueError(f"不支持的 Provider: {provider}")
