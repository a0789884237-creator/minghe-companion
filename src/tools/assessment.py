"""Psychological assessment tool."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AssessmentQuestion:
    """评估问题。"""

    id: str
    question: str
    options: List[Dict[str, Any]]
    category: str  # anxiety, depression, stress, etc.
    reverse_scored: bool = False


@dataclass
class AssessmentResult:
    """评估结果。"""

    assessment_type: str
    score: float
    severity: str  # minimal, mild, moderate, severe
    recommendations: List[str]
    risk_level: str  # low, medium, high

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。"""
        return {
            "assessment_type": self.assessment_type,
            "score": self.score,
            "severity": self.severity,
            "recommendations": self.recommendations,
            "risk_level": self.risk_level,
        }


class PsychologicalAssessmentTool:
    """心理评估工具。

    提供标准化的心理状态评估问卷，包括：
    - 焦虑自评量表 (SAS)
    - 抑郁自评量表 (SDS)
    - 压力感知量表 (PSS)
    - 简版心理弹性量表 (CD-RISC)
    """

    # 简化的评估问题示例（实际项目应使用完整的标准化量表）
    ASSESSMENT_TEMPLATES = {
        "anxiety": {
            "name": "焦虑自评量表",
            "description": "评估焦虑症状的严重程度",
            "questions": [
                {
                    "id": "anx_1",
                    "question": "我觉得比平时容易紧张和着急",
                    "category": "anxiety",
                    "options": [
                        {"value": 1, "label": "没有或很少时间"},
                        {"value": 2, "label": "小部分时间"},
                        {"value": 3, "label": "相当多时间"},
                        {"value": 4, "label": "绝大部分或全部时间"},
                    ],
                },
                {
                    "id": "anx_2",
                    "question": "我无缘无故地感到害怕",
                    "category": "anxiety",
                    "options": [
                        {"value": 1, "label": "没有或很少时间"},
                        {"value": 2, "label": "小部分时间"},
                        {"value": 3, "label": "相当多时间"},
                        {"value": 4, "label": "绝大部分或全部时间"},
                    ],
                },
                {
                    "id": "anx_3",
                    "question": "我容易心里烦乱或觉得惊恐",
                    "category": "anxiety",
                    "options": [
                        {"value": 1, "label": "没有或很少时间"},
                        {"value": 2, "label": "小部分时间"},
                        {"value": 3, "label": "相当多时间"},
                        {"value": 4, "label": "绝大部分或全部时间"},
                    ],
                },
            ],
        },
        "depression": {
            "name": "抑郁自评量表",
            "description": "评估抑郁症状的严重程度",
            "questions": [
                {
                    "id": "dep_1",
                    "question": "我感到情绪沮丧，郁闷",
                    "category": "depression",
                    "options": [
                        {"value": 1, "label": "没有或很少时间"},
                        {"value": 2, "label": "小部分时间"},
                        {"value": 3, "label": "相当多时间"},
                        {"value": 4, "label": "绝大部分或全部时间"},
                    ],
                },
                {
                    "id": "dep_2",
                    "question": "我感到早晨心情最好",
                    "category": "depression",
                    "reverse_scored": True,
                    "options": [
                        {"value": 4, "label": "没有或很少时间"},
                        {"value": 3, "label": "小部分时间"},
                        {"value": 2, "label": "相当多时间"},
                        {"value": 1, "label": "绝大部分或全部时间"},
                    ],
                },
                {
                    "id": "dep_3",
                    "question": "我感到自己什么都不好",
                    "category": "depression",
                    "options": [
                        {"value": 1, "label": "没有或很少时间"},
                        {"value": 2, "label": "小部分时间"},
                        {"value": 3, "label": "相当多时间"},
                        {"value": 4, "label": "绝大部分或全部时间"},
                    ],
                },
            ],
        },
        "stress": {
            "name": "压力感知量表",
            "description": "评估过去一个月的压力感知水平",
            "questions": [
                {
                    "id": "str_1",
                    "question": "在过去一个月里，有多少件事让你感到烦恼？",
                    "category": "stress",
                    "options": [
                        {"value": 0, "label": "没有"},
                        {"value": 1, "label": "很少"},
                        {"value": 2, "label": "有时"},
                        {"value": 3, "label": "经常"},
                        {"value": 4, "label": "总是"},
                    ],
                },
                {
                    "id": "str_2",
                    "question": "在过去一个月里，你有多少时候感到无法控制生活中的重要事情？",
                    "category": "stress",
                    "options": [
                        {"value": 0, "label": "从来没有"},
                        {"value": 1, "label": "几乎没有"},
                        {"value": 2, "label": "有时会"},
                        {"value": 3, "label": "经常会"},
                        {"value": 4, "label": "总是会"},
                    ],
                },
            ],
        },
    }

    # 评分阈值
    SEVERITY_THRESHOLDS = {
        "anxiety": {
            "minimal": (0, 29),
            "mild": (30, 39),
            "moderate": (40, 49),
            "severe": (50, 100),
        },
        "depression": {
            "minimal": (0, 29),
            "mild": (30, 39),
            "moderate": (40, 47),
            "severe": (48, 100),
        },
        "stress": {
            "low": (0, 13),
            "moderate": (14, 26),
            "high": (27, 40),
        },
    }

    def __init__(self):
        """初始化评估工具。"""
        self._assessment_history: Dict[str, List[AssessmentResult]] = {}

    def get_assessment_template(self, assessment_type: str) -> Dict[str, Any]:
        """获取评估问卷模板。

        Args:
            assessment_type: 评估类型 (anxiety/depression/stress)

        Returns:
            评估模板
        """
        return self.ASSESSMENT_TEMPLATES.get(assessment_type, {})

    def calculate_score(
        self, assessment_type: str, answers: Dict[str, int]
    ) -> AssessmentResult:
        """计算评估分数。

        Args:
            assessment_type: 评估类型
            answers: 用户答案 {question_id: value}

        Returns:
            评估结果
        """
        template = self.get_assessment_template(assessment_type)

        if not template:
            return AssessmentResult(
                assessment_type=assessment_type,
                score=0,
                severity="unknown",
                recommendations=[],
                risk_level="low",
            )

        questions = template.get("questions", [])

        # 计算总分
        total_score = 0
        max_score = 0

        for question in questions:
            question_id = question["id"]
            if question_id in answers:
                value = answers[question_id]

                # 处理反向计分
                if question.get("reverse_scored", False):
                    # 反向：选择最低值得最高分
                    max_option = max(opt["value"] for opt in question["options"])
                    value = (max_option + 1) - value

                total_score += value

            # 计算最大可能分数
            max_option = max(opt["value"] for opt in question["options"])
            max_score += max_option

        # 转换为百分制
        percentage = (total_score / max_score * 100) if max_score > 0 else 0

        # 确定严重程度
        severity = self._calculate_severity(assessment_type, percentage)

        # 生成建议
        recommendations = self._generate_recommendations(assessment_type, severity)

        # 确定风险等级
        risk_level = self._calculate_risk_level(severity)

        result = AssessmentResult(
            assessment_type=assessment_type,
            score=round(percentage, 1),
            severity=severity,
            recommendations=recommendations,
            risk_level=risk_level,
        )

        logger.info(
            f"Assessment completed: type={assessment_type}, "
            f"score={percentage}, severity={severity}"
        )

        return result

    def _calculate_severity(self, assessment_type: str, score: float) -> str:
        """计算严重程度。"""
        thresholds = self.SEVERITY_THRESHOLDS.get(assessment_type, {})

        for severity, (min_score, max_score) in thresholds.items():
            if min_score <= score <= max_score:
                return severity

        return "unknown"

    def _generate_recommendations(
        self, assessment_type: str, severity: str
    ) -> List[str]:
        """生成建议。"""

        recommendations_map = {
            "anxiety": {
                "minimal": [
                    "继续保持良好的生活习惯",
                    "规律作息和适量运动有助于维持心理健康",
                ],
                "mild": ["可以尝试一些放松技巧，如深呼吸", "建议关注压力源并尝试调整"],
                "moderate": [
                    "建议学习系统的焦虑管理技巧",
                    "可以考虑寻求心理咨询师的帮助",
                ],
                "severe": [
                    "建议尽快联系专业心理咨询师或医生",
                    "如果症状影响日常生活，请及时就医",
                ],
            },
            "depression": {
                "minimal": ["保持积极的生活态度和社交活动", "适度运动有助于提升情绪"],
                "mild": ["建议增加社交活动和兴趣爱好", "尝试记录感恩日记"],
                "moderate": ["建议寻求专业心理帮助", "可以尝试认知行为疗法"],
                "severe": ["强烈建议立即寻求专业帮助", "请联系心理咨询师或精神科医生"],
            },
            "stress": {
                "low": ["压力管理水平良好", "继续保持健康的生活方式"],
                "moderate": ["建议学习压力管理技巧", "尝试冥想或深呼吸练习"],
                "high": ["建议立即采取措施管理压力", "考虑寻求专业支持"],
            },
        }

        return recommendations_map.get(assessment_type, {}).get(
            severity, ["建议咨询专业人士"]
        )

    def _calculate_risk_level(self, severity: str) -> str:
        """计算风险等级。"""

        high_risk = ["moderate", "severe"]
        medium_risk = ["mild"]

        if severity in high_risk:
            return "high"
        elif severity in medium_risk:
            return "medium"

        return "low"

    def save_assessment_result(self, user_id: str, result: AssessmentResult) -> None:
        """保存评估结果。

        Args:
            user_id: 用户ID
            result: 评估结果
        """
        if user_id not in self._assessment_history:
            self._assessment_history[user_id] = []

        self._assessment_history[user_id].append(result)

    def get_assessment_history(
        self, user_id: str, assessment_type: Optional[str] = None
    ) -> List[AssessmentResult]:
        """获取评估历史。

        Args:
            user_id: 用户ID
            assessment_type: 可选的评估类型过滤

        Returns:
            评估结果列表
        """
        results = self._assessment_history.get(user_id, [])

        if assessment_type:
            results = [r for r in results if r.assessment_type == assessment_type]

        return results


# 全局实例
_assessment_tool: Optional[PsychologicalAssessmentTool] = None


def get_assessment_tool() -> PsychologicalAssessmentTool:
    """获取心理评估工具单例。"""
    global _assessment_tool
    if _assessment_tool is None:
        _assessment_tool = PsychologicalAssessmentTool()
    return _assessment_tool
