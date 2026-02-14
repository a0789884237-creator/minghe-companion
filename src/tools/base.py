"""Tool base classes and registry."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ToolResult:
    """工具执行结果。"""

    success: bool
    data: Any
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
        }


class BaseTool(ABC):
    """工具基类。"""

    name: str
    description: str

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """执行工具。

        Args:
            **kwargs: 工具参数

        Returns:
            ToolResult: 执行结果
        """
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """获取工具的JSON schema。

        Returns:
            工具的schema定义
        """
        pass


class ToolRegistry:
    """工具注册表。"""

    def __init__(self):
        """初始化工具注册表。"""
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """注册工具。

        Args:
            tool: 工具实例
        """
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        """获取工具。

        Args:
            name: 工具名称

        Returns:
            工具实例或None
        """
        return self._tools.get(name)

    def list_tools(self) -> list[Dict[str, Any]]:
        """列出所有工具。"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "schema": tool.get_schema(),
            }
            for tool in self._tools.values()
        ]

    def execute_tool(self, name: str, **kwargs) -> ToolResult:
        """执行工具。

        Args:
            name: 工具名称
            **kwargs: 工具参数

        Returns:
            执行结果
        """
        tool = self.get(name)
        if tool is None:
            return ToolResult(
                success=False, data=None, error=f"Tool '{name}' not found"
            )

        try:
            return tool.execute(**kwargs)
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))


from typing import Optional
