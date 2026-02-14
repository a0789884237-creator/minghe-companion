"""Crisis detection tool for mental health safety."""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from src.core.constants import (
    CRISIS_KEYWORDS,
    PROFESSIONAL_HOTLINES,
    RiskLevel,
)

logger = logging.getLogger(__name__)


@dataclass
class CrisisDetectionResult:
    """危机检测结果。"""

    detected: bool
    risk_level: RiskLevel
    category: Optional[str]
    matched_keywords: List[str]
    recommendation: str

    def to_dict(self) -> dict[str, str | bool | list[str] | None]:
        """转换为字典。"""
        return {
            "detected": self.detected,
            "risk_level": self.risk_level.value,
            "category": self.category,
            "matched_keywords": self.matched_keywords,
            "recommendation": self.recommendation,
        }


class CrisisDetector:
    """危机检测器。

    用于检测用户消息中的危机信号，包括自杀、自伤等高风险内容。
    这是心理健康Agent最重要的安全组件，必须具有最高优先级。
    """

    def __init__(
        self,
        keywords: Optional[Dict[str, List[str]]] = None,
        hotlines: Optional[Dict[str, str]] = None,
    ):
        """初始化危机检测器。

        Args:
            keywords: 自定义危机关键词字典
            hotlines: 自定义热线电话字典
        """
        self.keywords = keywords or CRISIS_KEYWORDS
        self.hotlines = hotlines or PROFESSIONAL_HOTLINES

        # 预编译正则表达式以提高性能
        self._compiled_patterns: dict[str, list[re.Pattern[str]]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """预编译所有关键词的正则表达式。"""
        for category, keyword_list in self.keywords.items():
            patterns: list[re.Pattern[str]] = []
            for keyword in keyword_list:
                # 使用正则表达式确保精确匹配
                try:
                    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                    patterns.append(pattern)
                except re.error as e:
                    logger.warning(f"Failed to compile keyword '{keyword}': {e}")
            self._compiled_patterns[category] = patterns

    def detect(self, message: str) -> CrisisDetectionResult:
        """检测消息中的危机信号。

        Args:
            message: 用户输入的消息

        Returns:
            CrisisDetectionResult: 包含检测结果和风险等级
        """
        if not message or not message.strip():
            return CrisisDetectionResult(
                detected=False,
                risk_level=RiskLevel.LOW,
                category=None,
                matched_keywords=[],
                recommendation="",
            )

        message_lower = message.lower()
        matched_keywords: List[str] = []
        detected_category: Optional[str] = None

        # 检查每个类别的关键词
        for category, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(message_lower):
                    matched_keywords.append(pattern.pattern)
                    if detected_category is None:
                        detected_category = category

        # 确定风险等级
        if detected_category is not None:
            risk_level = self._calculate_risk_level(detected_category, matched_keywords)
            recommendation = self._get_recommendation(risk_level)

            logger.warning(
                f"Crisis detected: category={detected_category}, "
                f"risk={risk_level.value}, keywords={matched_keywords}"
            )

            return CrisisDetectionResult(
                detected=True,
                risk_level=risk_level,
                category=detected_category,
                matched_keywords=matched_keywords,
                recommendation=recommendation,
            )

        return CrisisDetectionResult(
            detected=False,
            risk_level=RiskLevel.LOW,
            category=None,
            matched_keywords=[],
            recommendation="",
        )

    def _calculate_risk_level(
        self, category: str, matched_keywords: List[str]
    ) -> RiskLevel:
        """根据检测到的类别和关键词数量计算风险等级。"""

        # 自杀相关 - 最高风险
        if category == "suicide":
            if len(matched_keywords) >= 2:
                return RiskLevel.CRITICAL
            return RiskLevel.HIGH

        # 自伤相关 - 高风险
        if category == "self_harm":
            return RiskLevel.HIGH

        # 极端痛苦 - 中高风险
        if category == "extreme_distress":
            if len(matched_keywords) >= 2:
                return RiskLevel.HIGH
            return RiskLevel.MEDIUM

        return RiskLevel.MEDIUM

    def _get_recommendation(self, risk_level: RiskLevel) -> str:
        """根据风险等级获取建议。"""

        hotlines_text = "\n".join(
            f"- {name}: {phone}" for name, phone in self.hotlines.items()
        )

        recommendations = {
            RiskLevel.LOW: "继续正常对话",
            RiskLevel.MEDIUM: "给予情感支持，关注用户状态",
            RiskLevel.HIGH: "强烈建议寻求专业帮助，提供热线信息",
            RiskLevel.CRITICAL: "立即启动危机干预协议，确保用户安全",
        }

        base = recommendations.get(risk_level, "")

        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            return f"{base}\n\n专业热线：\n{hotlines_text}"

        return base

    def get_crisis_response(self, result: CrisisDetectionResult) -> str:
        """生成危机响应消息。

        Args:
            result: 危机检测结果

        Returns:
            适合发送给用户的危机响应消息
        """
        if not result.detected:
            return ""

        responses = {
            RiskLevel.CRITICAL: """我很担心你。

听到你这样说，我真的很在乎你。请你记住：

1. **你很重要** - 你的生命是宝贵的
2. **帮助是有的** - 专业的心理咨询师可以帮助你
3. **你不需要独自承受** - 有人愿意倾听和支持你

**请立即联系以下热线：**
{hotlines}

如果你有具体计划或想法，请告诉你信任的人，或者直接拨打上述热线。

记住：**你并不孤单，有人可以帮助你。**""",
            RiskLevel.HIGH: """我听到你了。

谢谢你愿意分享这些。我能感受到你现在的痛苦。重要的是：

- **你值得被帮助**
- **你的感受是重要的**
- **寻求帮助是勇敢的表现**

**专业支持可以帮到你：**
{hotlines}

如果你愿意，可以告诉我更多你的情况。或者，我建议你联系上面的热线，他们可以提供专业的支持。""",
            RiskLevel.MEDIUM: """感谢你告诉我这些。

我很高兴你愿意表达自己的感受。如果你觉得：
- 难以承受
- 需要更多支持

**可以考虑寻求专业帮助：**
{hotlines}

我在这里陪着你，你想聊些什么都可以。""",
        }

        hotlines_text = "\n".join(
            f"- {name}: {phone}" for name, phone in self.hotlines.items()
        )

        response_template = responses.get(
            result.risk_level, responses[RiskLevel.MEDIUM]
        )

        return response_template.format(hotlines=hotlines_text)

    def should_trigger_immediate_response(self, result: CrisisDetectionResult) -> bool:
        """判断是否需要立即响应。

        Args:
            result: 危机检测结果

        Returns:
            是否需要立即响应
        """
        return result.detected and result.risk_level in (
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        )


# 全局实例
_crisis_detector: Optional[CrisisDetector] = None


def get_crisis_detector() -> CrisisDetector:
    """获取危机检测器单例。"""
    global _crisis_detector
    if _crisis_detector is None:
        _crisis_detector = CrisisDetector()
    return _crisis_detector
