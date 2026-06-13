from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field

from app.core.logger import logger


class ToolNotFoundError(KeyError):
    """Raised when a requested tool is not registered."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Tool not found: {name}")


class ToolExecutionError(Exception):
    """Raised when tool execution fails."""

    def __init__(self, tool_name: str, message: str) -> None:
        self.tool_name = tool_name
        self.message = message
        super().__init__(f"{tool_name}: {message}")


class ToolResult(BaseModel):
    """Normalized result envelope returned by tool execution."""

    model_config = ConfigDict(extra="forbid")

    tool_name: str = Field(..., min_length=1)
    success: bool
    data: Any = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseTool(ABC):
    """Abstract async tool contract for agent tool-calling."""

    name: ClassVar[str]
    description: ClassVar[str]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls is BaseTool:
            return
        for attr in ("name", "description"):
            if not getattr(cls, attr, None):
                raise TypeError(f"{cls.__name__} must define class attribute '{attr}'")

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Run the tool with keyword arguments supplied by the caller."""


class ToolRegistry:
    """Registry for discovering and executing agent tools."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._logger = logger.getChild("tool_registry")

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool instance under its ``name``."""
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")

        self._tools[tool.name] = tool
        self._logger.debug("Registered tool", extra={"tool": tool.name})

    def get_tool(self, name: str) -> BaseTool:
        """Return a registered tool by name."""
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ToolNotFoundError(name) from exc

    async def execute_tool(
        self,
        name: str,
        **kwargs: Any,
    ) -> ToolResult:
        """Look up a tool by name, execute it, and return a ``ToolResult``."""
        tool = self.get_tool(name)
        self._logger.debug("Executing tool", extra={"tool": name})

        try:
            data = await tool.execute(**kwargs)
            return ToolResult(
                tool_name=name,
                success=True,
                data=data,
            )
        except ToolExecutionError as exc:
            return ToolResult(
                tool_name=name,
                success=False,
                error=exc.message,
            )
        except Exception as exc:
            return ToolResult(
                tool_name=name,
                success=False,
                error=str(exc),
            )
