"""Psychology Master Agent - 心理资讯大师."""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from src.core.constants import (
    IntentType,
    RiskLevel,
    InterventionType,
    AgeGroup,
)
from src.core.prompt import (
    build_agent_prompt,
    PSYCHOLOGY_MASTER_SYSTEM_PROMPT,
    CRISIS_RESPONSE_PROMPT,
    EMPATHY_RESPONSE_PROMPT,
    RAG_PROMPT_TEMPLATE,
)
from src.tools.crisis import CrisisDetector, get_crisis_detector
from src.tools.rag import KnowledgeBaseRetriever, get_knowledge_retriever
from src.tools.assessment import PsychologicalAssessmentTool, get_assessment_tool
from src.memory.system import MemorySystem, get_memory_system
from src.llm.client import ChatDeepSeek, get_llm_client

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Agent响应。"""

    content: str
    intent: IntentType
    risk_level: RiskLevel
    tools_used: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。"""
        return {
            "content": self.content,
            "intent": self.intent.value,
            "risk_level": self.risk_level.value,
            "tools_used": self.tools_used,
            "metadata": self.metadata,
        }


class PsychologyMasterAgent:
    """心理资讯大师Agent。

    核心功能：
    - 心理知识问答
    - 共情陪伴对话
    - CBT/正念干预引导
    - 心理评估辅助
    - 危机检测与干预
    """

    def __init__(
        self,
        crisis_detector: Optional[CrisisDetector] = None,
        knowledge_retriever: Optional[KnowledgeBaseRetriever] = None,
        assessment_tool: Optional[PsychologicalAssessmentTool] = None,
        memory_system: Optional[MemorySystem] = None,
        llm_client: Optional[ChatDeepSeek] = None,
    ):
        """初始化Agent。

        Args:
            crisis_detector: 危机检测器
            knowledge_retriever: 知识库检索器
            assessment_tool: 心理评估工具
            memory_system: 记忆系统
            llm_client: LLM客户端（GLM-4.7 Flash）
        """
        self.crisis_detector = crisis_detector or get_crisis_detector()
        self.knowledge_retriever = knowledge_retriever or get_knowledge_retriever()
        self.assessment_tool = assessment_tool or get_assessment_tool()
        self.memory_system = memory_system or get_memory_system()
        self.llm_client = llm_client

        # 生成session_id
        self.current_session_id = str(uuid.uuid4())

        logger.info("Psychology Master Agent initialized")

    def chat(
        self,
        user_id: str,
        message: str,
        session_id: Optional[str] = None,
    ) -> AgentResponse:
        """处理用户消息。

        Args:
            user_id: 用户ID
            message: 用户消息
            session_id: 会话ID（可选）

        Returns:
            AgentResponse: Agent响应
        """
        # 使用或创建会话ID
        session_id = session_id or self.current_session_id

        logger.info(
            f"Processing message: user_id={user_id}, "
            f"session_id={session_id}, message={message[:50]}..."
        )

        # 1. 危机检测（最高优先级）
        crisis_result = self.crisis_detector.detect(message)

        tools_used: List[str] = ["crisis_detection"]

        # 如果检测到危机，立即返回危机响应
        if crisis_result.detected:
            crisis_response = self.crisis_detector.get_crisis_response(crisis_result)

            # 保存交互
            self.memory_system.add_user_message(session_id, user_id, message)
            self.memory_system.add_assistant_message(
                session_id,
                user_id,
                crisis_response,
                intent=IntentType.CRISIS_SIGNAL.value,
            )

            return AgentResponse(
                content=crisis_response,
                intent=IntentType.CRISIS_SIGNAL,
                risk_level=crisis_result.risk_level,
                tools_used=tools_used,
                metadata={
                    "crisis_category": crisis_result.category,
                    "matched_keywords": ",".join(crisis_result.matched_keywords),
                },
            )

        # 2. 意图识别
        intent = self._classify_intent(message)
        tools_used.append("intent_classification")

        # 3. 根据意图处理
        response_content: str
        metadata: Dict[str, Any] = {}

        if intent == IntentType.KNOWLEDGE_QUERY:
            # 知识问答 - 使用RAG
            context = self._get_rag_context(message)
            response_content = self._generate_knowledge_response(message, context)
            tools_used.append("rag_retrieval")

        elif intent == IntentType.EMOTIONAL_SUPPORT:
            # 情感支持 - 共情对话
            response_content = self._generate_empathy_response(message)
            tools_used.append("empathy_response")

        elif intent == IntentType.HELP_SEEKING:
            # 寻求帮助 - 可能触发评估
            response_content = self._generate_help_response(message)

        elif intent == IntentType.PRACTICE_REQUEST:
            # 练习请求 - 引导干预
            response_content = self._generate_intervention_response(message)
            tools_used.append("intervention")

        else:
            # 一般对话
            response_content = self._generate_general_response(message)

        # 4. 保存交互到记忆
        self.memory_system.add_user_message(session_id, user_id, message)
        self.memory_system.add_assistant_message(
            session_id,
            user_id,
            response_content,
            intent=intent.value,
        )

        logger.info(
            f"Response generated: intent={intent.value}, "
            f"risk={crisis_result.risk_level.value}, "
            f"tools={tools_used}"
        )

        return AgentResponse(
            content=response_content,
            intent=intent,
            risk_level=crisis_result.risk_level,
            tools_used=tools_used,
            metadata=metadata,
        )

    def _classify_intent(self, message: str) -> IntentType:
        """识别用户意图。

        这是一个简化版的意图分类。
        生产环境应使用更复杂的分类器或LLM。

        Args:
            message: 用户消息

        Returns:
            IntentType: 识别的意图
        """
        message_lower = message.lower()

        # 知识问答关键词
        knowledge_keywords = ["是什么", "为什么", "如何", "怎么", "什么是", "解释"]
        if any(kw in message_lower for kw in knowledge_keywords):
            return IntentType.KNOWLEDGE_QUERY

        # 练习请求关键词
        practice_keywords = [
            "练习",
            "冥想",
            "深呼吸",
            "放松",
            "正念",
            "帮我",
            "教我",
            "我想做",
            "可以教",
        ]
        if any(kw in message_lower for kw in practice_keywords):
            return IntentType.PRACTICE_REQUEST

        # 寻求帮助关键词
        help_keywords = [
            "怎么办",
            "不知道怎么",
            "求助",
            "帮我",
            "很烦",
            "很痛苦",
            "难过",
            "抑郁",
            "焦虑",
        ]
        if any(kw in message_lower for kw in help_keywords):
            return IntentType.HELP_SEEKING

        # 情感倾诉（较长且包含情感词）
        emotion_keywords = [
            "心情",
            "感受",
            "情绪",
            "很难过",
            "很伤心",
            "压力",
            "烦恼",
            "倾诉",
            "说说",
        ]
        if any(kw in message_lower for kw in emotion_keywords):
            return IntentType.EMOTIONAL_SUPPORT

        return IntentType.GENERAL_CHAT

    def _get_rag_context(self, query: str) -> str:
        """获取RAG上下文。"""
        results = self.knowledge_retriever.retrieve(query, top_k=2)

        if not results:
            return ""

        contexts = []
        for result in results:
            contexts.append(
                f"【{result.metadata.get('description', '知识')}】\n{result.content}\n"
            )

        return "\n\n".join(contexts)

    def _generate_knowledge_response(self, query: str, context: str) -> str:
        """生成知识问答响应。

        Args:
            query: 用户问题
            context: RAG检索的上下文

        Returns:
            str: 响应内容
        """
        # 如果有LLM客户端，使用LLM生成响应
        if self.llm_client:
            try:
                prompt = RAG_PROMPT_TEMPLATE.format(context=context, question=query)
                messages = [
                    SystemMessage(content=PSYCHOLOGY_MASTER_SYSTEM_PROMPT),
                    HumanMessage(content=prompt),
                ]
                response = self.llm_client.invoke(messages)
                # 处理可能的复杂内容类型
                content = response.content
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    # 如果是列表，尝试提取字符串
                    for item in content:
                        if isinstance(item, str):
                            return item
                return str(content)
            except Exception as e:
                logger.warning(f"LLM调用失败，使用备用响应: {e}")

        # 备用响应（无LLM时）
        if context:
            return (
                f"我找到了一些相关的知识信息，供你参考：\n\n"
                f"{context}\n\n"
                f"希望这些信息对你有帮助。如果你有更多问题，欢迎继续问我。"
            )

        # 如果没有检索结果，使用通用响应
        return (
            "这是一个很好的问题。关于心理健康，"
            "我可以分享一些专业的知识。\n\n"
            "你具体想了解哪个方面呢？比如：\n"
            "- 压力管理技巧\n"
            "- 情绪调节方法\n"
            "- 焦虑/抑郁的应对方式\n"
            "- 心理疗愈技术\n\n"
            "请告诉我你想了解的内容，我会尽力帮助你。"
        )

    def _generate_empathy_response(self, message: str) -> str:
        """生成共情响应。

        Args:
            message: 用户消息

        Returns:
            str: 共情响应内容
        """
        # 如果有LLM客户端，使用LLM生成响应
        if self.llm_client:
            try:
                prompt = f"{EMPATHY_RESPONSE_PROMPT}\n\n用户说：{message}"
                messages = [
                    SystemMessage(content=PSYCHOLOGY_MASTER_SYSTEM_PROMPT),
                    HumanMessage(content=prompt),
                ]
                response = self.llm_client.invoke(messages)
                content = response.content
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, str):
                            return item
                return str(content)
            except Exception as e:
                logger.warning(f"LLM调用失败，使用备用响应: {e}")

        # 备用响应（无LLM时）
        response = "谢谢你愿意告诉我这些。我在这里倾听你。\n\n"
        response += (
            "如果你愿意，可以多说说你的想法和感受。\n"
            "或者，如果你需要一些帮助，我也可以提供一些"
            "情绪调节的小技巧。"
        )

        return response

    def _generate_help_response(self, message: str) -> str:
        """生成帮助请求响应。"""
        return (
            "我很理解你现在可能感到困难。\n\n"
            "首先，我想告诉你，能够寻求帮助是勇敢的第一步。\n\n"
            "我可以帮助你的是：\n"
            "1. 陪你聊聊，倾听你的心声\n"
            "2. 提供一些缓解情绪的技巧\n"
            "3. 如果你需要，可以帮你做一下心理状态评估\n"
            "4. 告诉你一些专业的求助渠道\n\n"
            "你现在最想获得什么样的帮助呢？"
        )

    def _generate_intervention_response(self, message: str) -> str:
        """生成干预响应。"""
        message_lower = message.lower()

        # 正念/冥想
        if "冥想" in message_lower or "正念" in message_lower:
            return (
                "当然可以！让我带你进行一次简单的正念练习。\n\n"
                "【5分钟正念呼吸练习】\n\n"
                "1. 找一个安静的地方，坐下来或躺下来\n"
                "2. 闭上眼睛，慢慢地深呼吸\n"
                "3. 关注你的呼吸，感受空气从鼻子进入，再从嘴巴呼出\n"
                "4. 如果走神了，没关系，轻轻地把注意力带回呼吸\n"
                "5. 继续这样深呼吸5分钟\n\n"
                "完成后，慢慢睁开眼睛。\n\n"
                "你感觉怎么样？"
            )

        # 深呼吸
        if "呼吸" in message_lower or "放松" in message_lower:
            return (
                "好的，让我们做一个放松练习。\n\n"
                "【4-7-8 呼吸法】\n\n"
                "1. 用鼻子吸气，数4下（1、2、3、4）\n"
                "2. 屏住呼吸，数7下（1、2、3、4、5、6、7）\n"
                "3. 用嘴巴慢慢呼气，数8下（1、2、3、4、5、6、7、8）\n"
                "4. 重复这个过程3-4次\n\n"
                "这个方法可以帮助你平静下来。\n\n"
                "做完后告诉我感觉如何？"
            )

        # CBT练习
        if "认知" in message_lower or "cbt" in message_lower or "思维" in message_lower:
            return (
                "好的，让我们做一个简单的CBT练习。\n\n"
                "【思维记录表】\n\n"
                "当你有负面情绪时，试着记录：\n\n"
                "1. **情境**：发生了什么？\n"
                "2. **想法**：你当时在想什么？\n"
                "3. **情绪**：你感受到什么情绪？（1-10分）\n"
                "4. **证据**：支持这个想法的证据是什么？\n"
                "5. **反证**：有什么证据其实不支持这个想法？\n"
                "6. **新的想法**：更平衡的想法是什么？\n"
                "7. **新的情绪**：现在情绪几分？\n\n"
                "你可以试着用这个方法记录一下。\n"
                "需要我陪你一起做吗？"
            )

        return (
            "我可以引导你进行一些心理练习。\n\n"
            "你希望尝试哪种类型的练习？\n"
            "1. 正念冥想 - 帮助平静心绪\n"
            "2. 呼吸放松 - 缓解紧张焦虑\n"
            "3. CBT练习 - 改变负性思维\n"
            "4. 情绪记录 - 了解自己的情绪模式\n\n"
            "请告诉我你的选择。"
        )

    def _generate_general_response(self, message: str) -> str:
        """生成一般对话响应。

        Args:
            message: 用户消息

        Returns:
            str: 一般对话响应
        """
        logger.info(f"LLM client in _generate_general_response: {self.llm_client}")
        # 如果有LLM客户端，使用LLM生成响应
        if self.llm_client:
            logger.info("Using LLM for response generation")
            try:
                prompt = f"用户说：{message}\n\n请给出温暖、专业的回应。"
                messages = [
                    SystemMessage(content=PSYCHOLOGY_MASTER_SYSTEM_PROMPT),
                    HumanMessage(content=prompt),
                ]
                response = self.llm_client.invoke(messages)
                content = response.content
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, str):
                            return item
                return str(content)
            except Exception as e:
                logger.warning(f"LLM调用失败，使用备用响应: {e}")

        # 备用响应（无LLM时）
        return (
            "我在这里倾听你。\n\n"
            "你可以告诉我：\n"
            "- 你的感受和想法\n"
            "- 困惑你的问题\n"
            "- 想要了解的心理知识\n"
            "- 需要帮助的方面\n\n"
            "我会尽力帮助你。"
        )


# 全局实例
_agent: Optional[PsychologyMasterAgent] = None


def get_psychology_master_agent(
    llm_client: Optional[ChatDeepSeek] = None,
) -> PsychologyMasterAgent:
    """获取Agent单例。

    Args:
        llm_client: 可选的LLM客户端

    Returns:
        PsychologyMasterAgent: Agent实例
    """
    global _agent
    print(
        f"DEBUG get_psychology_master_agent: _agent={_agent}, llm_client={llm_client}"
    )
    if _agent is None:
        print("DEBUG: Creating new agent")
        _agent = PsychologyMasterAgent(llm_client=llm_client)
    elif llm_client is not None:
        print("DEBUG: Updating existing agent's LLM client")
        _agent.llm_client = llm_client
    return _agent
