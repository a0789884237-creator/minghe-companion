"""Core constants for Minghe Companion."""

from enum import Enum


class AgeGroup(str, Enum):
    """年龄段枚举。"""

    ADOLESCENT = "adolescent"  # 13-18岁
    YOUNG_ADULT = "young_adult"  # 18-35岁
    MIDDLE_ADULT = "middle_adult"  # 35-60岁
    SENIOR = "senior"  # 60岁以上


class RiskLevel(str, Enum):
    """危机风险等级。"""

    LOW = "low"  # 一般情绪困扰
    MEDIUM = "medium"  # 持续负面情绪
    HIGH = "high"  # 明显痛苦信号
    CRITICAL = "critical"  # 危机信号


class IntentType(str, Enum):
    """用户意图类型。"""

    KNOWLEDGE_QUERY = "knowledge_query"  # 知识问答
    EMOTIONAL_SUPPORT = "emotional_support"  # 情感倾诉
    HELP_SEEKING = "help_seeking"  # 寻求帮助
    PRACTICE_REQUEST = "practice_request"  # 练习请求
    CRISIS_SIGNAL = "crisis_signal"  # 危机信号
    GENERAL_CHAT = "general_chat"  # 闲聊


class InterventionType(str, Enum):
    """干预类型。"""

    CBT_EXERCISE = "cbt_exercise"  # CBT认知行为练习
    MINDFULNESS = "mindfulness"  # 正念训练
    EMOTION_REGULATION = "emotion_regulation"  # 情绪调节


# 危机关键词（必须定期更新）
CRISIS_KEYWORDS = {
    "suicide": [
        "自杀",
        "想死",
        "不想活了",
        "结束生命",
        "zs",
        "suicide",
        "不想活了",
        "活够了",
        "死了一了百了",
        "死了就好了",
    ],
    "self_harm": [
        "自伤",
        "割腕",
        "伤害自己",
        "self-harm",
        "si",
        "想割腕",
        "想伤害自己",
        "想自残",
    ],
    "extreme_distress": [
        "崩溃",
        "彻底绝望",
        "活着没意思",
        "没意义",
        "无法忍受",
        "撑不住了",
        "受够了",
        "极度绝望",
        "绝望",
        "无助",
    ],
}

# 专业心理援助热线
PROFESSIONAL_HOTLINES = {
    "全国心理援助热线": "400-161-9995",
    "生命热线": "400-821-1215",
    "北京心理危机研究与干预中心": "010-82951332",
    "希望24热线": "400-161-9995",
}

# 年龄段描述
AGE_GROUP_DESCRIPTIONS = {
    AgeGroup.ADOLESCENT: {
        "name": "青少年",
        "age_range": "13-18岁",
        "characteristics": "自我认同发展、学业压力、同伴关系",
        "communication_style": "平等尊重、避免说教、轻松自然",
    },
    AgeGroup.YOUNG_ADULT: {
        "name": "青年",
        "age_range": "18-35岁",
        "characteristics": "职业发展、人际关系、生活压力",
        "communication_style": "理解压力、实用建议、尊重独立",
    },
    AgeGroup.MIDDLE_ADULT: {
        "name": "中年",
        "age_range": "35-60岁",
        "characteristics": "家庭责任、职业瓶颈、中年危机",
        "communication_style": "尊重经验、平衡视角、务实建议",
    },
    AgeGroup.SENIOR: {
        "name": "老年",
        "age_range": "60岁以上",
        "characteristics": "退休适应、健康关注、孤独感",
        "communication_style": "耐心温和、回忆引导、价值认可",
    },
}

# 默认Agent配置
DEFAULT_AGENT_CONFIG = {
    "max_conversation_turns": 50,
    "short_term_memory_tokens": 8000,
    "temperature": 0.7,
    "max_tokens": 2000,
    "enable_memory": True,
    "enable_rag": True,
    "enable_crisis_detection": True,
}
