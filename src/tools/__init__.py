"""Tools module for Minghe Companion."""

from src.tools.base import BaseTool, ToolResult, ToolRegistry
from src.tools.crisis import CrisisDetector, CrisisDetectionResult, get_crisis_detector
from src.tools.rag import (
    KnowledgeBaseRetriever,
    RetrievalResult,
    get_knowledge_retriever,
)
from src.tools.assessment import (
    PsychologicalAssessmentTool,
    AssessmentResult,
    get_assessment_tool,
)

__all__ = [
    # Base
    "BaseTool",
    "ToolResult",
    "ToolRegistry",
    # Crisis
    "CrisisDetector",
    "CrisisDetectionResult",
    "get_crisis_detector",
    # RAG
    "KnowledgeBaseRetriever",
    "RetrievalResult",
    "get_knowledge_retriever",
    # Assessment
    "PsychologicalAssessmentTool",
    "AssessmentResult",
    "get_assessment_tool",
]
