"""Tests for crisis detection tool."""

import pytest

from src.core.constants import RiskLevel
from src.tools.crisis import CrisisDetector, CrisisDetectionResult, get_crisis_detector


class TestCrisisDetector:
    """危机检测器测试。"""

    def test_suicide_keyword_detection(self):
        """测试自杀关键词检测。"""
        detector = CrisisDetector()
        result = detector.detect("我不想活了")

        assert result.detected is True
        assert result.category == "suicide"
        assert result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert len(result.matched_keywords) > 0

    def test_suicide_keyword_critical_level(self):
        """测试自杀多个关键词 - CRITICAL级别。"""
        detector = CrisisDetector()
        result = detector.detect("我不想活了活着太累了想死")

        assert result.detected is True
        assert result.category == "suicide"
        assert result.risk_level == RiskLevel.CRITICAL

    def test_self_harm_keyword_detection(self):
        """测试自伤关键词检测。"""
        detector = CrisisDetector()
        result = detector.detect("我想伤害自己")

        assert result.detected is True
        assert result.category == "self_harm"
        assert result.risk_level == RiskLevel.HIGH

    def test_extreme_distress_detection(self):
        """测试极端痛苦关键词检测。"""
        detector = CrisisDetector()
        result = detector.detect("我感到极度绝望和无助")

        assert result.detected is True
        assert result.category == "extreme_distress"

    def test_normal_message_returns_low_risk(self):
        """测试正常消息返回低风险。"""
        detector = CrisisDetector()
        result = detector.detect("今天天气真好")

        assert result.detected is False
        assert result.risk_level == RiskLevel.LOW

    def test_empty_message_returns_low_risk(self):
        """测试空消息返回低风险。"""
        detector = CrisisDetector()
        result = detector.detect("")

        assert result.detected is False
        assert result.risk_level == RiskLevel.LOW

    def test_crisis_with_recommendation(self):
        """测试危机检测结果包含建议。"""
        detector = CrisisDetector()
        result = detector.detect("我不想活了")

        assert result.detected is True
        assert result.recommendation != ""

    def test_should_trigger_immediate_response(self):
        """测试是否需要立即响应。"""
        detector = CrisisDetector()

        result_high = detector.detect("我想自杀")
        assert detector.should_trigger_immediate_response(result_high) is True

        result_low = detector.detect("今天很开心")
        assert detector.should_trigger_immediate_response(result_low) is False

    def test_get_crisis_response(self):
        """测试生成危机响应消息。"""
        detector = CrisisDetector()
        result = detector.detect("我不想活了")

        response = detector.get_crisis_response(result)
        assert response != ""
        assert "帮助" in response or "热线" in response

    def test_singleton_pattern(self):
        """测试单例模式。"""
        detector1 = get_crisis_detector()
        detector2 = get_crisis_detector()

        assert detector1 is detector2
