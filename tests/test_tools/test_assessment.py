"""Tests for psychological assessment tool."""

import pytest
from src.tools.assessment import (
    PsychologicalAssessmentTool,
    AssessmentQuestion,
    AssessmentResult,
    get_assessment_tool,
)


class TestAssessmentQuestion:
    """AssessmentQuestion dataclass tests."""

    def test_creation(self):
        """测试评估问题创建。"""
        question = AssessmentQuestion(
            id="test_1",
            question="测试问题",
            options=[{"value": 1, "label": "选项1"}],
            category="anxiety",
            reverse_scored=False,
        )

        assert question.id == "test_1"
        assert question.question == "测试问题"
        assert question.category == "anxiety"
        assert question.reverse_scored is False


class TestAssessmentResult:
    """AssessmentResult dataclass tests."""

    def test_creation(self):
        """测试评估结果创建。"""
        result = AssessmentResult(
            assessment_type="anxiety",
            score=75.5,
            severity="severe",
            recommendations=["建议就医"],
            risk_level="high",
        )

        assert result.assessment_type == "anxiety"
        assert result.score == 75.5
        assert result.severity == "severe"
        assert result.risk_level == "high"

    def test_to_dict(self):
        """测试转换为字典。"""
        result = AssessmentResult(
            assessment_type="depression",
            score=35.0,
            severity="mild",
            recommendations=["建议咨询"],
            risk_level="medium",
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["assessment_type"] == "depression"
        assert result_dict["score"] == 35.0
        assert result_dict["severity"] == "mild"
        assert result_dict["risk_level"] == "medium"


class TestPsychologicalAssessmentTool:
    """PsychologicalAssessmentTool tests."""

    @pytest.fixture
    def assessment_tool(self) -> PsychologicalAssessmentTool:
        """创建评估工具实例。"""
        return PsychologicalAssessmentTool()

    def test_initialization(self, assessment_tool: PsychologicalAssessmentTool):
        """测试初始化。"""
        assert assessment_tool is not None
        assert assessment_tool._assessment_history == {}

    def test_get_assessment_template_anxiety(
        self, assessment_tool: PsychologicalAssessmentTool
    ):
        """测试获取焦虑评估模板。"""
        template = assessment_tool.get_assessment_template("anxiety")

        assert template["name"] == "焦虑自评量表"
        assert len(template["questions"]) == 3

    def test_get_assessment_template_depression(
        self, assessment_tool: PsychologicalAssessmentTool
    ):
        """测试获取抑郁评估模板。"""
        template = assessment_tool.get_assessment_template("depression")

        assert template["name"] == "抑郁自评量表"
        assert len(template["questions"]) == 3

    def test_get_assessment_template_stress(
        self, assessment_tool: PsychologicalAssessmentTool
    ):
        """测试获取压力评估模板。"""
        template = assessment_tool.get_assessment_template("stress")

        assert template["name"] == "压力感知量表"
        assert len(template["questions"]) == 2

    def test_get_assessment_template_not_found(
        self, assessment_tool: PsychologicalAssessmentTool
    ):
        """测试获取不存在的评估模板。"""
        template = assessment_tool.get_assessment_template("invalid_type")

        assert template == {}

    def test_calculate_score_anxiety_minimal(
        self, assessment_tool: PsychologicalAssessmentTool
    ):
        """测试焦虑评估 - 最低分。"""
        # 所有问题都选最低分 (1)
        answers = {
            "anx_1": 1,
            "anx_2": 1,
            "anx_3": 1,
        }

        result = assessment_tool.calculate_score("anxiety", answers)

        assert result.assessment_type == "anxiety"
        assert result.severity == "minimal"
        assert result.risk_level == "low"

    def test_calculate_score_anxiety_severe(
        self, assessment_tool: PsychologicalAssessmentTool
    ):
        """测试焦虑评估 - 严重。"""
        # 所有问题都选最高分 (4)
        answers = {
            "anx_1": 4,
            "anx_2": 4,
            "anx_3": 4,
        }

        result = assessment_tool.calculate_score("anxiety", answers)

        assert result.assessment_type == "anxiety"
        assert result.severity == "severe"
        assert result.risk_level == "high"

    def test_calculate_score_depression_with_reverse(
        self, assessment_tool: PsychologicalAssessmentTool
    ):
        """测试抑郁评估 - 包含反向计分。"""
        # dep_2 是反向计分题目
        # 如果选"没有或很少时间"(value=4)，反向后应该是 1
        answers = {
            "dep_1": 1,
            "dep_2": 4,  # 反向计分
            "dep_3": 1,
        }

        result = assessment_tool.calculate_score("depression", answers)

        # 分数计算: 1 + (5-4) + 1 = 3
        # 最大分数: 4 + 4 + 4 = 12
        # 百分比: 3/12 * 100 = 25
        assert result.assessment_type == "depression"
        assert result.severity == "minimal"

    def test_calculate_score_depression_moderate(
        self, assessment_tool: PsychologicalAssessmentTool
    ):
        """测试抑郁评估 - 不同分数对应不同严重程度。"""
        # 测试低分 - minimal
        answers_low = {
            "dep_1": 1,
            "dep_2": 4,  # 反向计分后变成1
            "dep_3": 1,
        }
        result = assessment_tool.calculate_score("depression", answers_low)
        # 1 + 1 + 1 = 3, 3/12*100 = 25, minimal
        assert result.severity == "minimal"

        # 测试高分 - severe
        answers_high = {
            "dep_1": 4,
            "dep_2": 1,  # 反向计分后变成4
            "dep_3": 4,
        }
        result = assessment_tool.calculate_score("depression", answers_high)
        # 4 + 4 + 4 = 12, 12/12*100 = 100, severe
        assert result.severity == "severe"

    def test_calculate_severity_out_of_range(
        self, assessment_tool: PsychologicalAssessmentTool
    ):
        """测试超出范围的分数。"""
        # 超出范围的分数返回 "unknown"
        assert assessment_tool._calculate_severity("anxiety", -10) == "unknown"
        assert assessment_tool._calculate_severity("anxiety", 150) == "unknown"

    def test_generate_recommendations_anxiety(
        self, assessment_tool: PsychologicalAssessmentTool
    ):
        """测试焦虑建议生成。"""
        minimal = assessment_tool._generate_recommendations("anxiety", "minimal")
        assert len(minimal) > 0
        assert "继续保持良好的生活习惯" in minimal

        severe = assessment_tool._generate_recommendations("anxiety", "severe")
        assert len(severe) > 0
        assert "建议尽快联系专业心理咨询师或医生" in severe

    def test_generate_recommendations_depression(
        self, assessment_tool: PsychologicalAssessmentTool
    ):
        """测试抑郁建议生成。"""
        moderate = assessment_tool._generate_recommendations("depression", "moderate")
        assert len(moderate) > 0
        assert "建议寻求专业心理帮助" in moderate

    def test_generate_recommendations_stress(
        self, assessment_tool: PsychologicalAssessmentTool
    ):
        """测试压力建议生成。"""
        high = assessment_tool._generate_recommendations("stress", "high")
        assert len(high) > 0

    def test_generate_recommendations_unknown(
        self, assessment_tool: PsychologicalAssessmentTool
    ):
        """测试未知类型的建议。"""
        recommendations = assessment_tool._generate_recommendations(
            "unknown", "unknown"
        )
        assert recommendations == ["建议咨询专业人士"]

    def test_calculate_risk_level(self, assessment_tool: PsychologicalAssessmentTool):
        """测试风险等级计算。"""
        assert assessment_tool._calculate_risk_level("minimal") == "low"
        assert assessment_tool._calculate_risk_level("mild") == "medium"
        assert assessment_tool._calculate_risk_level("moderate") == "high"
        assert assessment_tool._calculate_risk_level("severe") == "high"

    def test_save_assessment_result(self, assessment_tool: PsychologicalAssessmentTool):
        """测试保存评估结果。"""
        result = AssessmentResult(
            assessment_type="anxiety",
            score=50.0,
            severity="severe",
            recommendations=["建议就医"],
            risk_level="high",
        )

        assessment_tool.save_assessment_result("user_123", result)

        history = assessment_tool.get_assessment_history("user_123")
        assert len(history) == 1
        assert history[0].score == 50.0

    def test_save_multiple_results(self, assessment_tool: PsychologicalAssessmentTool):
        """测试保存多个评估结果。"""
        result1 = AssessmentResult(
            assessment_type="anxiety",
            score=30.0,
            severity="mild",
            recommendations=[],
            risk_level="medium",
        )
        result2 = AssessmentResult(
            assessment_type="depression",
            score=25.0,
            severity="minimal",
            recommendations=[],
            risk_level="low",
        )

        assessment_tool.save_assessment_result("user_123", result1)
        assessment_tool.save_assessment_result("user_123", result2)

        history = assessment_tool.get_assessment_history("user_123")
        assert len(history) == 2

    def test_get_assessment_history(self, assessment_tool: PsychologicalAssessmentTool):
        """测试获取评估历史。"""
        result1 = AssessmentResult(
            assessment_type="anxiety",
            score=30.0,
            severity="mild",
            recommendations=[],
            risk_level="medium",
        )
        result2 = AssessmentResult(
            assessment_type="depression",
            score=25.0,
            severity="minimal",
            recommendations=[],
            risk_level="low",
        )

        assessment_tool.save_assessment_result("user_123", result1)
        assessment_tool.save_assessment_result("user_123", result2)

        # 获取所有
        history = assessment_tool.get_assessment_history("user_123")
        assert len(history) == 2

        # 按类型过滤
        anxiety_history = assessment_tool.get_assessment_history("user_123", "anxiety")
        assert len(anxiety_history) == 1
        assert anxiety_history[0].assessment_type == "anxiety"

    def test_get_assessment_history_no_results(
        self, assessment_tool: PsychologicalAssessmentTool
    ):
        """测试无评估历史。"""
        history = assessment_tool.get_assessment_history("nonexistent_user")
        assert history == []


class TestPsychologicalAssessmentToolSingleton:
    """测试心理评估工具单例模式。"""

    def test_singleton_pattern(self):
        """测试单例模式。"""
        # 重置全局实例
        import src.tools.assessment

        src.tools.assessment._assessment_tool = None

        tool1 = get_assessment_tool()
        tool2 = get_assessment_tool()

        assert tool1 is tool2
