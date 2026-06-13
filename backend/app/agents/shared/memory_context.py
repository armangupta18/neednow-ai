from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ContextScope = Literal["short_term", "long_term", "preferences", "summary"]
ClearScope = Literal["short_term", "long_term", "preferences", "summary", "all"]


class MemoryContext(BaseModel):
    """In-session memory container for agent orchestration and prompt assembly."""

    model_config = ConfigDict(extra="forbid")

    short_term_memory: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Recent, session-scoped context entries",
    )
    long_term_memory: dict[str, Any] = Field(
        default_factory=dict,
        description="Durable facts retained across turns",
    )
    user_preferences: dict[str, Any] = Field(
        default_factory=dict,
        description="User-specific preference signals for personalization",
    )
    conversation_summary: str | None = Field(
        default=None,
        description="Rolling summary of the active conversation",
    )

    def add_context(
        self,
        key: str,
        value: Any,
        *,
        scope: ContextScope = "short_term",
    ) -> None:
        """Add or update context in the selected memory scope."""
        if scope == "short_term":
            self.short_term_memory.append({"key": key, "value": value})
            return

        if scope == "long_term":
            self.long_term_memory[key] = value
            return

        if scope == "preferences":
            self.user_preferences[key] = value
            return

        self.conversation_summary = str(value) if value is not None else None

    def get_context(
        self,
        *,
        scope: ContextScope | Literal["all"] = "all",
    ) -> dict[str, Any]:
        """Return context for one scope or the full memory snapshot."""
        if scope == "short_term":
            return {"short_term_memory": list(self.short_term_memory)}

        if scope == "long_term":
            return {"long_term_memory": dict(self.long_term_memory)}

        if scope == "preferences":
            return {"user_preferences": dict(self.user_preferences)}

        if scope == "summary":
            return {"conversation_summary": self.conversation_summary}

        return {
            "short_term_memory": list(self.short_term_memory),
            "long_term_memory": dict(self.long_term_memory),
            "user_preferences": dict(self.user_preferences),
            "conversation_summary": self.conversation_summary,
        }

    def clear_context(
        self,
        *,
        scope: ClearScope = "short_term",
    ) -> None:
        """Clear context for one scope or reset all memory fields."""
        if scope in ("short_term", "all"):
            self.short_term_memory.clear()

        if scope in ("long_term", "all"):
            self.long_term_memory.clear()

        if scope in ("preferences", "all"):
            self.user_preferences.clear()

        if scope in ("summary", "all"):
            self.conversation_summary = None
