"""Tests for memory system."""

import pytest
from datetime import datetime

from src.memory.system import (
    Message,
    UserProfile,
    ShortTermMemory,
    LongTermMemory,
    MemorySystem,
    get_memory_system,
)


class TestMessage:
    """Message dataclass tests."""

    def test_creation(self):
        """测试消息创建。"""
        message = Message(
            role="user",
            content="你好",
            metadata={"intent": "greeting"},
        )

        assert message.role == "user"
        assert message.content == "你好"
        assert message.metadata["intent"] == "greeting"
        assert isinstance(message.timestamp, datetime)


class TestUserProfile:
    """UserProfile dataclass tests."""

    def test_creation(self):
        """测试用户画像创建。"""
        profile = UserProfile(
            user_id="user_123",
            age_group="adult",
            name="张三",
        )

        assert profile.user_id == "user_123"
        assert profile.age_group == "adult"
        assert profile.name == "张三"
        assert isinstance(profile.created_at, datetime)

    def test_default_values(self):
        """测试默认值。"""
        profile = UserProfile(user_id="user_456")

        assert profile.age_group == "young_adult"
        assert profile.name is None
        assert profile.preferences == {}
        assert profile.characteristics == []


class TestShortTermMemory:
    """ShortTermMemory tests."""

    @pytest.fixture
    def short_memory(self) -> ShortTermMemory:
        """创建短期记忆实例。"""
        return ShortTermMemory(max_messages=5)

    def test_initialization(self, short_memory: ShortTermMemory):
        """测试初始化。"""
        assert short_memory.max_messages == 5
        assert short_memory.get_session_count() == 0

    def test_add_message(self, short_memory: ShortTermMemory):
        """测试添加消息。"""
        short_memory.add_message(
            session_id="session_1",
            role="user",
            content="你好",
        )

        messages = short_memory.get_messages("session_1")
        assert len(messages) == 1
        assert messages[0].content == "你好"

    def test_add_multiple_messages(self, short_memory: ShortTermMemory):
        """测试添加多条消息。"""
        for i in range(3):
            short_memory.add_message(
                session_id="session_1",
                role="user",
                content=f"消息{i}",
            )

        messages = short_memory.get_messages("session_1")
        assert len(messages) == 3

    def test_trim_session(self, short_memory: ShortTermMemory):
        """测试会话修剪。"""
        # max_messages = 5
        for i in range(8):
            short_memory.add_message(
                session_id="session_1",
                role="user",
                content=f"消息{i}",
            )

        messages = short_memory.get_messages("session_1")
        # 应该是5条消息
        assert len(messages) == 5

    def test_trim_preserves_system_messages(self):
        """测试修剪保留系统消息。"""
        memory = ShortTermMemory(max_messages=3)

        # 添加系统消息
        memory.add_message(
            session_id="session_1",
            role="system",
            content="系统提示",
        )

        # 添加用户消息
        for i in range(5):
            memory.add_message(
                session_id="session_1",
                role="user",
                content=f"用户消息{i}",
            )

        messages = memory.get_messages("session_1")
        # 应该保留系统消息 + 最近3条
        assert len(messages) == 4
        assert messages[0].role == "system"

    def test_get_messages_exclude_system(self, short_memory: ShortTermMemory):
        """测试获取消息排除系统消息。"""
        short_memory.add_message(
            session_id="session_1",
            role="system",
            content="系统提示",
        )
        short_memory.add_message(
            session_id="session_1",
            role="user",
            content="用户消息",
        )

        messages = short_memory.get_messages("session_1", include_system=False)
        assert len(messages) == 1
        assert messages[0].role == "user"

    def test_get_conversation_context(self, short_memory: ShortTermMemory):
        """测试获取对话上下文。"""
        short_memory.add_message(
            session_id="session_1",
            role="user",
            content="你好",
        )
        short_memory.add_message(
            session_id="session_1",
            role="assistant",
            content="你好，有什么可以帮您？",
        )

        context = short_memory.get_conversation_context("session_1")

        assert "用户: 你好" in context
        assert "助手: 你好" in context

    def test_get_conversation_context_empty(self, short_memory: ShortTermMemory):
        """测试空会话的对话上下文。"""
        context = short_memory.get_conversation_context("nonexistent_session")
        assert context == ""

    def test_get_conversation_context_last_n(self, short_memory: ShortTermMemory):
        """测试获取最近n条消息。"""
        for i in range(15):
            short_memory.add_message(
                session_id="session_1",
                role="user",
                content=f"消息{i}",
            )

        context = short_memory.get_conversation_context("session_1", last_n=3)

        # 应该只包含最后3条
        assert "消息12" in context
        assert "消息14" in context

    def test_clear_session(self, short_memory: ShortTermMemory):
        """测试清除会话。"""
        short_memory.add_message(
            session_id="session_1",
            role="user",
            content="测试",
        )

        short_memory.clear_session("session_1")

        messages = short_memory.get_messages("session_1")
        assert len(messages) == 0

    def test_get_session_count(self, short_memory: ShortTermMemory):
        """测试获取会话数。"""
        short_memory.add_message(
            session_id="session_1",
            role="user",
            content="测试1",
        )
        short_memory.add_message(
            session_id="session_2",
            role="user",
            content="测试2",
        )

        assert short_memory.get_session_count() == 2


class TestLongTermMemory:
    """LongTermMemory tests."""

    @pytest.fixture
    def long_memory(self) -> LongTermMemory:
        """创建长期记忆实例。"""
        return LongTermMemory()

    def test_initialization(self, long_memory: LongTermMemory):
        """测试初始化。"""
        assert long_memory._profiles == {}
        assert long_memory._interaction_history == {}

    def test_get_or_create_profile(self, long_memory: LongTermMemory):
        """测试获取或创建用户画像。"""
        profile = long_memory.get_or_create_profile("user_123")

        assert profile.user_id == "user_123"
        assert profile.age_group == "young_adult"

    def test_get_or_create_existing(self, long_memory: LongTermMemory):
        """测试获取已存在的用户画像。"""
        profile1 = long_memory.get_or_create_profile("user_123")
        profile2 = long_memory.get_or_create_profile("user_123")

        assert profile1 is profile2

    def test_update_profile(self, long_memory: LongTermMemory):
        """测试更新用户画像。"""
        profile = long_memory.update_profile(
            "user_123",
            name="张三",
            age_group="adult",
        )

        assert profile.name == "张三"
        assert profile.age_group == "adult"

    def test_get_profile(self, long_memory: LongTermMemory):
        """测试获取用户画像。"""
        long_memory.update_profile("user_123", name="李四")

        profile = long_memory.get_profile("user_123")

        assert profile is not None
        assert profile.name == "李四"

    def test_get_profile_not_exists(self, long_memory: LongTermMemory):
        """测试获取不存在的用户画像。"""
        profile = long_memory.get_profile("nonexistent_user")
        assert profile is None

    def test_save_interaction(self, long_memory: LongTermMemory):
        """测试保存交互记录。"""
        long_memory.save_interaction(
            user_id="user_123",
            message="你好",
            response="你好",
            intent="greeting",
            emotion="neutral",
        )

        history = long_memory.get_recent_interactions("user_123")
        assert len(history) == 1
        assert history[0]["message"] == "你好"
        assert history[0]["intent"] == "greeting"

    def test_save_multiple_interactions(self, long_memory: LongTermMemory):
        """测试保存多条交互记录。"""
        for i in range(5):
            long_memory.save_interaction(
                user_id="user_123",
                message=f"消息{i}",
                response=f"回复{i}",
            )

        history = long_memory.get_recent_interactions("user_123")
        assert len(history) == 5

    def test_get_recent_interactions(self, long_memory: LongTermMemory):
        """测试获取最近交互记录。"""
        for i in range(15):
            long_memory.save_interaction(
                user_id="user_123",
                message=f"消息{i}",
                response=f"回复{i}",
            )

        recent = long_memory.get_recent_interactions("user_123", limit=3)
        assert len(recent) == 3

    def test_search_memory(self, long_memory: LongTermMemory):
        """测试搜索记忆。"""
        long_memory.save_interaction(
            user_id="user_123",
            message="我最近感到焦虑",
            response="我理解你的感受",
        )
        long_memory.save_interaction(
            user_id="user_123",
            message="睡眠不好",
            response="这可能影响你的情绪",
        )

        results = long_memory.search_memory("user_123", "焦虑")

        assert len(results) >= 1

    def test_search_memory_no_results(self, long_memory: LongTermMemory):
        """测试搜索无结果。"""
        results = long_memory.search_memory("user_123", "不存在的内容")
        assert results == []

    def test_get_memory_summary(self, long_memory: LongTermMemory):
        """测试获取记忆摘要。"""
        long_memory.save_interaction(
            user_id="user_123",
            message="测试",
            response="回复",
            intent="test",
            emotion="neutral",
        )

        # 需要保存10条才会更新摘要
        for i in range(9):
            long_memory.save_interaction(
                user_id="user_123",
                message=f"消息{i}",
                response=f"回复{i}",
                intent="test",
                emotion="neutral",
            )

        summary = long_memory.get_memory_summary("user_123")
        assert "交互次数" in summary


class TestMemorySystem:
    """MemorySystem tests."""

    @pytest.fixture
    def memory_system(self) -> MemorySystem:
        """创建记忆系统实例。"""
        return MemorySystem(max_short_term_messages=10)

    def test_initialization(self, memory_system: MemorySystem):
        """测试初始化。"""
        assert isinstance(memory_system.short_term, ShortTermMemory)
        assert isinstance(memory_system.long_term, LongTermMemory)

    def test_add_user_message(self, memory_system: MemorySystem):
        """测试添加用户消息。"""
        memory_system.add_user_message(
            session_id="session_1",
            user_id="user_123",
            content="你好",
        )

        messages = memory_system.short_term.get_messages("session_1")
        assert len(messages) == 1
        assert messages[0].role == "user"
        assert messages[0].content == "你好"

    def test_add_assistant_message(self, memory_system: MemorySystem):
        """测试添加助手消息。"""
        memory_system.add_assistant_message(
            session_id="session_1",
            user_id="user_123",
            content="你好，有什么可以帮您？",
            intent="greeting",
            emotion="neutral",
        )

        messages = memory_system.short_term.get_messages("session_1")
        assert len(messages) == 1
        assert messages[0].role == "assistant"

        # 检查长期记忆
        history = memory_system.long_term.get_recent_interactions("user_123")
        assert len(history) == 1

    def test_get_conversation_context(self, memory_system: MemorySystem):
        """测试获取对话上下文。"""
        # 添加一些消息
        memory_system.add_user_message(
            session_id="session_1",
            user_id="user_123",
            content="我最近压力大",
        )
        memory_system.add_assistant_message(
            session_id="session_1",
            user_id="user_123",
            content="我理解，能详细说说吗？",
        )

        context = memory_system.get_conversation_context(
            session_id="session_1",
            user_id="user_123",
        )

        assert "我最近压力大" in context

    def test_get_user_profile(self, memory_system: MemorySystem):
        """测试获取用户画像。"""
        profile = memory_system.get_user_profile("user_123")

        assert profile.user_id == "user_123"

    def test_update_user_profile(self, memory_system: MemorySystem):
        """测试更新用户画像。"""
        profile = memory_system.update_user_profile(
            "user_123",
            name="张三",
            age_group="adult",
        )

        assert profile.name == "张三"
        assert profile.age_group == "adult"


class TestMemorySystemSingleton:
    """测试记忆系统单例模式。"""

    def test_singleton_pattern(self):
        """测试单例模式。"""
        # 重置全局实例
        import src.memory.system

        src.memory.system._memory_system = None

        system1 = get_memory_system()
        system2 = get_memory_system()

        assert system1 is system2
