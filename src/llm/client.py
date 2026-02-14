"""LLM Client for DeepSeek Chat."""

import logging
import os
from typing import Any, Dict, List, Optional

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain.chat_models.base import BaseChatModel
from pydantic import Field

logger = logging.getLogger(__name__)


class ChatDeepSeek(BaseChatModel):
    """DeepSeek Chat model.

    使用DeepSeek API进行对话生成。
    """

    model_name: str = Field(default="deepseek-chat", description="模型名称")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int = Field(default=2000, ge=1, le=16384, description="最大生成token数")
    api_key: Optional[str] = Field(default=None, description="API密钥")
    base_url: str = Field(default="https://api.deepseek.com", description="API基础URL")

    def __init__(self, **data: Any):
        """初始化LLM客户端。"""
        super().__init__(**data)
        if not self.api_key:
            # 先尝试环境变量
            self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            # 再尝试从配置文件读取
            from src.core.config import get_settings

            settings = get_settings()
            self.api_key = settings.deepseek_api_key

    @property
    def _llm_type(self) -> str:
        """返回LLM类型标识。"""
        return "deepseek_chat"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """生成聊天响应。"""
        import requests

        logger.info(
            f"DeepSeek _generate called with {len(messages)} messages, api_key set: {bool(self.api_key)}"
        )

        if not self.api_key:
            logger.error("DEEPSEEK_API_KEY is not set!")
            raise ValueError("DEEPSEEK_API_KEY未设置，请在.env文件中配置")

        try:
            # 转换消息格式
            deepseek_messages = self._convert_messages(messages)

            # 调用API
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "messages": deepseek_messages,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "stop": stop,
                },
                timeout=60,
            )

            if response.status_code != 200:
                logger.error(
                    f"DeepSeek API错误: {response.status_code} {response.text}"
                )
                raise Exception(f"API错误: {response.status_code}")

            result = response.json()

            # 解析响应
            content = result["choices"][0]["message"]["content"]

            # 构建ChatResult
            message = HumanMessage(content=content)
            generation = ChatGeneration(message=message)

            return ChatResult(generations=[generation])

        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {e}")
            raise

    def _convert_messages(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """转换消息格式为DeepSeek API所需格式。"""
        deepseek_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                deepseek_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                deepseek_messages.append({"role": "user", "content": msg.content})
            else:
                deepseek_messages.append({"role": "user", "content": str(msg.content)})
        return deepseek_messages

    def _llm_used_kwargs(self) -> Dict[str, Any]:
        """返回LLM使用的额外参数。"""
        return {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    @classmethod
    def from_llm(cls, **kwargs: Any) -> "ChatDeepSeek":
        """从LLM创建实例的便捷方法。"""
        return cls(**kwargs)


# 全局LLM实例
_llm_instance: Optional[ChatDeepSeek] = None


def get_llm_client(
    temperature: float = 0.7,
    max_tokens: int = 2000,
    model_name: str = "deepseek-chat",
) -> ChatDeepSeek:
    """获取LLM客户端单例。

    Args:
        temperature: 温度参数
        max_tokens: 最大token数
        model_name: 模型名称

    Returns:
        ChatDeepSeek: LLM客户端实例
    """
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = ChatDeepSeek(
            temperature=temperature,
            max_tokens=max_tokens,
            model_name=model_name,
        )
    return _llm_instance


def reset_llm_client() -> None:
    """重置LLM客户端（用于测试）。"""
    global _llm_instance
    _llm_instance = None
