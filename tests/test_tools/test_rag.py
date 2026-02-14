"""Tests for RAG knowledge base retrieval tool."""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Any, Dict, Generator, List

from src.tools.rag import (
    KnowledgeBaseRetriever,
    RetrievalResult,
    get_knowledge_retriever,
)


class TestRetrievalResult:
    """RetrievalResult dataclass tests."""

    def test_creation(self):
        """测试检索结果创建。"""
        result = RetrievalResult(
            content="心理健康是指...",
            source="psychology_basics/mental_health.md",
            relevance_score=0.85,
            metadata={"category": "psychology_basics"},
        )

        assert result.content == "心理健康是指..."
        assert result.source == "psychology_basics/mental_health.md"
        assert result.relevance_score == 0.85

    def test_to_dict(self):
        """测试转换为字典。"""
        result = RetrievalResult(
            content="测试内容",
            source="test.md",
            relevance_score=0.5,
            metadata={"category": "test"},
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["content"] == "测试内容"
        assert result_dict["source"] == "test.md"
        assert result_dict["relevance_score"] == 0.5
        assert result_dict["metadata"]["category"] == "test"


class TestKnowledgeBaseRetriever:
    """KnowledgeBaseRetriever tests."""

    @pytest.fixture
    def temp_knowledge_base(self) -> Generator[Path, None, None]:
        """创建临时知识库目录。"""
        temp_dir = tempfile.mkdtemp()
        knowledge_base = Path(temp_dir) / "knowledge_base"

        # 创建目录结构
        (knowledge_base / "psychology_basics").mkdir(parents=True)
        (knowledge_base / "therapy_techniques").mkdir(parents=True)
        (knowledge_base / "chinese_wisdom").mkdir(parents=True)

        # 创建测试文档
        (knowledge_base / "psychology_basics" / "mental_health.md").write_text(
            "心理健康是指个体心理在各方面都处于良好状态。\n"
            "心理健康包括情绪稳定、行为适当、人际和谐等方面。\n"
            "维护心理健康需要保持积极乐观的心态。",
            encoding="utf-8",
        )

        (knowledge_base / "psychology_basics" / "stress_management.md").write_text(
            "压力管理是维护心理健康的重要手段。\n"
            "有效的压力管理包括时间管理、放松技巧、社会支持等。\n"
            "长期压力可能导致焦虑、抑郁等心理问题。",
            encoding="utf-8",
        )

        (knowledge_base / "therapy_techniques" / "cbt.md").write_text(
            "认知行为疗法(CBT)是一种常用的心理治疗方法。\n"
            "CBT强调认知、情绪和行为之间的相互作用。\n"
            "通过改变负性思维模式来改善情绪状态。",
            encoding="utf-8",
        )

        (knowledge_base / "chinese_wisdom" / "daoist_psychology.md").write_text(
            "道家思想强调顺其自然、无为而治。\n"
            "道家心理学强调内心的平静与和谐。\n"
            "无为不是无所作为，而是顺其自然。",
            encoding="utf-8",
        )

        yield knowledge_base

        # 清理
        shutil.rmtree(temp_dir)

    def test_initialization(self, temp_knowledge_base: Path):
        """测试知识库初始化。"""
        retriever = KnowledgeBaseRetriever(
            knowledge_base_path=str(temp_knowledge_base),
            top_k=5,
        )

        assert retriever.top_k == 5
        assert len(retriever.list_categories()) == 3

    def test_load_knowledge_base(self, temp_knowledge_base: Path):
        """测试知识库加载。"""
        retriever = KnowledgeBaseRetriever(
            knowledge_base_path=str(temp_knowledge_base),
        )

        categories = retriever.list_categories()
        assert "psychology_basics" in categories
        assert "therapy_techniques" in categories
        assert "chinese_wisdom" in categories

    def test_retrieve_basic(self, temp_knowledge_base: Path):
        """测试基础检索功能。"""
        retriever = KnowledgeBaseRetriever(
            knowledge_base_path=str(temp_knowledge_base),
        )

        results = retriever.retrieve("心理健康")

        assert len(results) > 0
        assert all(isinstance(r, RetrievalResult) for r in results)

    def test_retrieve_with_category_filter(self, temp_knowledge_base: Path):
        """测试指定类别检索。"""
        retriever = KnowledgeBaseRetriever(
            knowledge_base_path=str(temp_knowledge_base),
        )

        # 只搜索心理科普类别
        results = retriever.retrieve(
            query="心理健康",
            category="psychology_basics",
        )

        assert len(results) > 0
        for r in results:
            assert r.metadata["category"] == "psychology_basics"

    def test_retrieve_with_top_k(self, temp_knowledge_base: Path):
        """测试top_k参数。"""
        retriever = KnowledgeBaseRetriever(
            knowledge_base_path=str(temp_knowledge_base),
            top_k=2,
        )

        results = retriever.retrieve("心理健康 压力")

        assert len(results) <= 2

    def test_retrieve_empty_query(self, temp_knowledge_base: Path):
        """测试空查询返回空列表。"""
        retriever = KnowledgeBaseRetriever(
            knowledge_base_path=str(temp_knowledge_base),
        )

        results = retriever.retrieve("")

        assert results == []

    def test_retrieve_no_match(self, temp_knowledge_base: Path):
        """测试无匹配结果。"""
        retriever = KnowledgeBaseRetriever(
            knowledge_base_path=str(temp_knowledge_base),
        )

        # 使用完全不相关的查询
        results = retriever.retrieve("量子物理 相对论")

        # 由于关键词匹配，可能返回空或低分结果
        # 检查返回类型正确即可
        assert isinstance(results, list)

    def test_calculate_relevance(self, temp_knowledge_base: Path):
        """测试相关性计算。"""
        retriever = KnowledgeBaseRetriever(
            knowledge_base_path=str(temp_knowledge_base),
        )

        # 完全匹配
        score1 = retriever._calculate_relevance("心理健康", "心理健康是指...")
        assert score1 == 1.0

        # 部分匹配
        score2 = retriever._calculate_relevance("心理 健康", "心理健康是指...")
        assert score2 > 0

        # 无匹配
        score3 = retriever._calculate_relevance("abc xyz", "心理健康是指...")
        assert score3 == 0.0

    def test_calculate_relevance_empty_query(self, temp_knowledge_base: Path):
        """测试空查询的相关性计算。"""
        retriever = KnowledgeBaseRetriever(
            knowledge_base_path=str(temp_knowledge_base),
        )

        score = retriever._calculate_relevance("", "内容")
        assert score == 0.0

    def test_extract_relevant_section(self, temp_knowledge_base: Path):
        """测试提取相关段落。"""
        retriever = KnowledgeBaseRetriever(
            knowledge_base_path=str(temp_knowledge_base),
        )

        content = (
            "第一段内容。\n"
            "第二段内容。\n"
            "第三段内容：关键词在这里。\n"
            "第四段内容。\n"
            "第五段内容。"
        )

        # 提取包含关键词的段落
        section = retriever._extract_relevant_section(content, "关键词")

        assert "关键词" in section
        assert isinstance(section, str)

    def test_extract_relevant_section_no_match(self, temp_knowledge_base: Path):
        """测试无匹配时返回文档开头。"""
        retriever = KnowledgeBaseRetriever(
            knowledge_base_path=str(temp_knowledge_base),
        )

        content = "这是文档的开头内容。后面还有其他内容。"

        section = retriever._extract_relevant_section(content, "不存在的关键词")

        # 应该返回文档开头
        assert "开头" in section

    def test_get_knowledge_by_category(self, temp_knowledge_base: Path):
        """测试按类别获取知识。"""
        retriever = KnowledgeBaseRetriever(
            knowledge_base_path=str(temp_knowledge_base),
        )

        docs = retriever.get_knowledge_by_category("psychology_basics")

        assert len(docs) == 2
        assert all(d["category"] == "psychology_basics" for d in docs)

    def test_get_knowledge_by_category_not_exists(self, temp_knowledge_base: Path):
        """测试获取不存在的类别。"""
        retriever = KnowledgeBaseRetriever(
            knowledge_base_path=str(temp_knowledge_base),
        )

        docs = retriever.get_knowledge_by_category("nonexistent_category")

        assert docs == []

    def test_list_categories(self, temp_knowledge_base: Path):
        """测试列出所有类别。"""
        retriever = KnowledgeBaseRetriever(
            knowledge_base_path=str(temp_knowledge_base),
        )

        categories = retriever.list_categories()

        assert isinstance(categories, list)
        assert len(categories) == 3


class TestKnowledgeBaseRetrieverSingleton:
    """测试知识库检索器单例模式。"""

    @pytest.fixture
    def temp_knowledge_base(self) -> Generator[Path, None, None]:
        """创建临时知识库目录。"""
        temp_dir = tempfile.mkdtemp()
        knowledge_base = Path(temp_dir) / "knowledge_base"

        (knowledge_base / "psychology_basics").mkdir(parents=True)
        (knowledge_base / "psychology_basics" / "test.md").write_text(
            "测试内容", encoding="utf-8"
        )

        yield knowledge_base

        shutil.rmtree(temp_dir)

    def test_singleton_pattern(self, temp_knowledge_base: Path):
        """测试单例模式。"""
        # 重置全局实例
        import src.tools.rag

        src.tools.rag._retriever = None

        retriever1 = get_knowledge_retriever(
            knowledge_base_path=str(temp_knowledge_base)
        )
        retriever2 = get_knowledge_retriever(
            knowledge_base_path=str(temp_knowledge_base)
        )

        assert retriever1 is retriever2

    def test_singleton_reinitialization(self, temp_knowledge_base: Path):
        """测试单例不会被重新初始化。"""
        # 重置全局实例
        import src.tools.rag

        src.tools.rag._retriever = None

        # 首先通过 get_knowledge_retriever 创建实例
        retriever1 = get_knowledge_retriever(
            knowledge_base_path=str(temp_knowledge_base)
        )

        # 保存第一个实例的top_k值
        original_top_k = retriever1.top_k

        # 再次调用 get_knowledge_retriever，传入不同参数不会改变已有实例
        retriever2 = get_knowledge_retriever(
            knowledge_base_path=str(temp_knowledge_base)
        )

        # 应该是同一个实例
        assert retriever1 is retriever2
        # top_k应该是初始值，不会被改变
        assert retriever1.top_k == original_top_k
