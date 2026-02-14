"""RAG knowledge base retrieval tool."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """检索结果。"""

    content: str
    source: str
    relevance_score: float
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict:
        """转换为字典。"""
        return {
            "content": self.content,
            "source": self.source,
            "relevance_score": self.relevance_score,
            "metadata": self.metadata,
        }


class KnowledgeBaseRetriever:
    """知识库检索器。

    用于从心理健康知识库中检索相关内容，支持多种知识类型：
    - 心理科普知识
    - 心理治疗技术
    - 中国传统文化心理智慧
    - 危机干预资源
    """

    def __init__(
        self,
        knowledge_base_path: str = "knowledge_base",
        top_k: int = 3,
    ):
        """初始化知识库检索器。

        Args:
            knowledge_base_path: 知识库文件路径
            top_k: 返回最相关的k个结果
        """
        self.knowledge_base_path = Path(knowledge_base_path)
        self.top_k = top_k
        self._knowledge_cache: Dict[str, List[Dict[str, Any]]] = {}

        # 初始化知识库
        self._load_knowledge_base()

    def _load_knowledge_base(self) -> None:
        """加载知识库内容。"""

        # 定义知识库类别
        knowledge_categories = {
            "psychology_basics": "心理科普知识",
            "therapy_techniques": "心理治疗技术",
            "chinese_wisdom": "中国传统文化心理智慧",
            "crisis_resources": "危机干预资源",
        }

        for category, description in knowledge_categories.items():
            category_path = self.knowledge_base_path / category

            if not category_path.exists():
                logger.warning(f"Knowledge category not found: {category_path}")
                continue

            documents = []

            # 加载该类别下的所有文档
            for file_path in category_path.glob("*.md"):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    documents.append(
                        {
                            "content": content,
                            "source": str(
                                file_path.relative_to(self.knowledge_base_path)
                            ),
                            "category": category,
                            "description": description,
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to load {file_path}: {e}")

            if documents:
                self._knowledge_cache[category] = documents

        logger.info(
            f"Loaded knowledge base: "
            f"{len(self._knowledge_cache)} categories, "
            f"{sum(len(docs) for docs in self._knowledge_cache.values())} documents"
        )

    def retrieve(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> List[RetrievalResult]:
        """检索与查询相关的内容。

        Args:
            query: 用户查询
            category: 指定知识类别（可选）
            top_k: 返回结果数量

        Returns:
            检索结果列表
        """
        results: List[RetrievalResult] = []
        k = top_k or self.top_k

        # 确定要搜索的类别
        categories_to_search = (
            [category] if category else list(self._knowledge_cache.keys())
        )

        for cat in categories_to_search:
            if cat not in self._knowledge_cache:
                continue

            # 简单关键词匹配（生产环境应使用向量相似度）
            for doc in self._knowledge_cache[cat]:
                content = doc["content"]
                query_lower = query.lower()

                # 计算简单相关性分数
                score = self._calculate_relevance(query_lower, content)

                if score > 0:
                    results.append(
                        RetrievalResult(
                            content=self._extract_relevant_section(content, query),
                            source=doc["source"],
                            relevance_score=score,
                            metadata={
                                "category": doc["category"],
                                "description": doc["description"],
                            },
                        )
                    )

        # 按相关性排序
        results.sort(key=lambda x: x.relevance_score, reverse=True)

        return results[:k]

    def _calculate_relevance(self, query: str, content: str) -> float:
        """计算查询与内容的简单相关性分数。

        生产环境应使用向量嵌入进行语义相似度计算。

        Args:
            query: 查询关键词
            content: 文档内容

        Returns:
            相关性分数 0-1
        """
        content_lower = content.lower()
        query_words = query.split()

        if not query_words:
            return 0.0

        # 计算查询词在内容中出现的次数
        match_count = sum(1 for word in query_words if word in content_lower)

        # 归一化分数
        return min(match_count / len(query_words), 1.0)

    def _extract_relevant_section(
        self, content: str, query: str, context_chars: int = 500
    ) -> str:
        """提取与查询最相关的文档部分。

        Args:
            content: 完整文档内容
            query: 用户查询
            context_chars: 提取的上下文字符数

        Returns:
            相关部分的内容
        """
        query_words = query.lower().split()

        # 找到第一个相关词的位置
        content_lower = content.lower()
        first_match_pos = -1

        for word in query_words:
            pos = content_lower.find(word)
            if pos != -1:
                first_match_pos = pos
                break

        if first_match_pos == -1:
            # 如果没有精确匹配，返回文档开头
            return content[:context_chars]

        # 提取上下文
        start = max(0, first_match_pos - context_chars // 2)
        end = min(len(content), first_match_pos + context_chars)

        section = content[start:end]

        # 清理提取的内容
        if start > 0:
            section = "..." + section
        if end < len(content):
            section = section + "..."

        return section

    def get_knowledge_by_category(self, category: str) -> List[Dict[str, Any]]:
        """获取指定类别的所有知识。

        Args:
            category: 知识类别

        Returns:
            知识文档列表
        """
        return self._knowledge_cache.get(category, [])

    def list_categories(self) -> List[str]:
        """列出所有可用的知识类别。"""
        return list(self._knowledge_cache.keys())


# 全局实例
_retriever: Optional[KnowledgeBaseRetriever] = None


def get_knowledge_retriever(
    knowledge_base_path: str = "knowledge_base",
) -> KnowledgeBaseRetriever:
    """获取知识库检索器单例。"""
    global _retriever
    if _retriever is None:
        _retriever = KnowledgeBaseRetriever(knowledge_base_path=knowledge_base_path)
    return _retriever
