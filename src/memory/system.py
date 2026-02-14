"""Memory system for conversation context."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """对话消息。"""

    role: str  # user / assistant / system
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserProfile:
    """用户画像。"""

    user_id: str
    age_group: str = "young_adult"
    name: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    characteristics: List[str] = field(default_factory=list)
    common_stressors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class ShortTermMemory:
    """短期记忆 - 当前会话上下文。

    存储当前对话的消息历史，用于维护对话连贯性。
    """

    def __init__(
        self,
        max_messages: int = 50,
        max_tokens: int = 8000,
    ):
        """初始化短期记忆。

        Args:
            max_messages: 最大保留消息数
            max_tokens: 最大token数（近似）
        """
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self._sessions: Dict[str, List[Message]] = {}

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """添加消息到会话。

        Args:
            session_id: 会话ID
            role: 角色 (user/assistant/system)
            content: 消息内容
            metadata: 附加元数据
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = []

        message = Message(role=role, content=content, metadata=metadata or {})

        self._sessions[session_id].append(message)

        # 修剪过长的会话
        self._trim_session(session_id)

    def _trim_session(self, session_id: str) -> None:
        """修剪会话以保持大小合理。"""
        session = self._sessions[session_id]

        # 限制消息数量
        if len(session) > self.max_messages:
            # 保留最近的消息和系统提示
            system_messages = [m for m in session if m.role == "system"]
            other_messages = [m for m in session if m.role != "system"]

            self._sessions[session_id] = (
                system_messages + other_messages[-self.max_messages :]
            )

    def get_messages(
        self, session_id: str, include_system: bool = True
    ) -> List[Message]:
        """获取会话消息。

        Args:
            session_id: 会话ID
            include_system: 是否包含系统消息

        Returns:
            消息列表
        """
        messages = self._sessions.get(session_id, [])

        if not include_system:
            messages = [m for m in messages if m.role != "system"]

        return messages

    def get_conversation_context(self, session_id: str, last_n: int = 10) -> str:
        """获取对话上下文摘要。

        Args:
            session_id: 会话ID
            last_n: 获取最近n条消息

        Returns:
            格式化的对话上下文
        """
        messages = self.get_messages(session_id, include_system=True)

        if not messages:
            return ""

        recent_messages = messages[-last_n:]

        context_parts = []
        for msg in recent_messages:
            role_label = "用户" if msg.role == "user" else "助手"
            context_parts.append(f"{role_label}: {msg.content}")

        return "\n".join(context_parts)

    def clear_session(self, session_id: str) -> None:
        """清除会话。"""
        if session_id in self._sessions:
            del self._sessions[session_id]

    def get_session_count(self) -> int:
        """获取活跃会话数。"""
        return len(self._sessions)


class LongTermMemory:
    """长期记忆 - 跨会话用户画像。

    存储用户的长期信息，包括偏好、历史交互摘要等。
    """

    def __init__(self):
        """初始化长期记忆。"""
        self._profiles: Dict[str, UserProfile] = {}
        self._interaction_history: Dict[str, List[Dict[str, Any]]] = {}
        self._memory_summary: Dict[str, str] = {}  # 用户记忆摘要

    def get_or_create_profile(self, user_id: str) -> UserProfile:
        """获取或创建用户画像。

        Args:
            user_id: 用户ID

        Returns:
            用户画像
        """
        if user_id not in self._profiles:
            self._profiles[user_id] = UserProfile(user_id=user_id)

        return self._profiles[user_id]

    def update_profile(self, user_id: str, **kwargs) -> UserProfile:
        """更新用户画像。

        Args:
            user_id: 用户ID
            **kwargs: 要更新的字段

        Returns:
            更新后的用户画像
        """
        profile = self.get_or_create_profile(user_id)

        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        profile.updated_at = datetime.now()

        return profile

    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """获取用户画像。"""
        return self._profiles.get(user_id)

    def save_interaction(
        self,
        user_id: str,
        message: str,
        response: str,
        intent: Optional[str] = None,
        emotion: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """保存交互记录。

        Args:
            user_id: 用户ID
            message: 用户消息
            response: 助手回复
            intent: 识别的意图
            emotion: 检测到的情绪
            metadata: 附加元数据
        """
        if user_id not in self._interaction_history:
            self._interaction_history[user_id] = []

        record = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "response": response,
            "intent": intent,
            "emotion": emotion,
            "metadata": metadata or {},
        }

        self._interaction_history[user_id].append(record)

        # 定期更新记忆摘要
        if len(self._interaction_history[user_id]) % 10 == 0:
            self._update_memory_summary(user_id)

    def _update_memory_summary(self, user_id: str) -> None:
        """更新用户记忆摘要。"""
        history = self._interaction_history.get(user_id, [])

        if not history:
            return

        # 提取关键信息
        intents = [h["intent"] for h in history if h.get("intent")]
        emotions = [h["emotion"] for h in history if h.get("emotion")]

        # 生成摘要（简化版，生产环境应使用LLM生成）
        summary_parts = []

        if intents:
            top_intents = ", ".join(set(intents[-5:]))
            summary_parts.append(f"常见意图: {top_intents}")

        if emotions:
            top_emotions = ", ".join(set(emotions[-5:]))
            summary_parts.append(f"近期情绪: {top_emotions}")

        summary_parts.append(f"交互次数: {len(history)}")

        self._memory_summary[user_id] = "; ".join(summary_parts)

    def get_memory_summary(self, user_id: str) -> str:
        """获取用户记忆摘要。"""
        return self._memory_summary.get(user_id, "")

    def get_recent_interactions(
        self, user_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取最近的交互记录。"""
        history = self._interaction_history.get(user_id, [])
        return history[-limit:] if history else []

    def search_memory(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        """搜索用户记忆。

        简化版实现，生产环境应使用向量检索。

        Args:
            user_id: 用户ID
            query: 查询关键词

        Returns:
            相关的交互记录
        """
        history = self._interaction_history.get(user_id, [])
        query_lower = query.lower()

        results = []
        for record in history:
            if (
                query_lower in record.get("message", "").lower()
                or query_lower in record.get("response", "").lower()
            ):
                results.append(record)

        return results[-10:]  # 返回最近10条


class MemorySystem:
    """统一的记忆系统。

    整合短期记忆和长期记忆，提供统一的记忆接口。
    """

    def __init__(
        self,
        max_short_term_messages: int = 50,
        max_short_term_tokens: int = 8000,
    ):
        """初始化记忆系统。"""
        self.short_term = ShortTermMemory(
            max_messages=max_short_term_messages,
            max_tokens=max_short_term_tokens,
        )
        self.long_term = LongTermMemory()

    def add_user_message(
        self,
        session_id: str,
        user_id: str,
        content: str,
    ) -> None:
        """添加用户消息。"""
        self.short_term.add_message(
            session_id=session_id,
            role="user",
            content=content,
        )

    def add_assistant_message(
        self,
        session_id: str,
        user_id: str,
        content: str,
        intent: Optional[str] = None,
        emotion: Optional[str] = None,
    ) -> None:
        """添加助手消息。"""
        self.short_term.add_message(
            session_id=session_id,
            role="assistant",
            content=content,
            metadata={"intent": intent, "emotion": emotion},
        )

        # 保存到长期记忆
        self.long_term.save_interaction(
            user_id=user_id,
            message="",  # 用户消息已在上一步保存
            response=content,
            intent=intent,
            emotion=emotion,
        )

    def get_conversation_context(
        self,
        session_id: str,
        user_id: str,
    ) -> str:
        """获取完整的对话上下文。"""
        # 获取短期记忆
        short_context = self.short_term.get_conversation_context(
            session_id=session_id, last_n=10
        )

        # 获取长期记忆摘要
        long_summary = self.long_term.get_memory_summary(user_id)

        # 组合上下文
        context_parts = []

        if long_summary:
            context_parts.append(f"【用户历史】{long_summary}")

        if short_context:
            context_parts.append(f"【当前对话】\n{short_context}")

        return "\n\n".join(context_parts)

    def get_user_profile(self, user_id: str) -> UserProfile:
        """获取用户画像。"""
        return self.long_term.get_or_create_profile(user_id)

    def update_user_profile(self, user_id: str, **kwargs) -> UserProfile:
        """更新用户画像。"""
        return self.long_term.update_profile(user_id, **kwargs)


# 全局实例
_memory_system: Optional[MemorySystem] = None


def get_memory_system() -> MemorySystem:
    """获取记忆系统单例。"""
    global _memory_system
    if _memory_system is None:
        _memory_system = MemorySystem()
    return _memory_system
