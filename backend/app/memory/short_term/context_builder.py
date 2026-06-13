from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.logger import logger
from app.memory.short_term.session_memory import (
    InteractionLog,
    SessionMemory,
    SessionMemoryManager,
)

logger = logging.getLogger(__name__)


class ContextRole(str, Enum):
    """Role in conversation context."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ContextMessage(BaseModel):
    """Single message in context."""

    model_config = ConfigDict(extra="forbid")

    role: ContextRole
    content: str = Field(..., min_length=1)
    timestamp: datetime | None = None
    metadata: dict = Field(default_factory=dict)


class ConversationContext(BaseModel):
    """Complete conversation context for LLM."""

    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    user_id: UUID
    messages: list[ContextMessage] = Field(default_factory=list)
    system_context: str | None = None
    metadata: dict = Field(default_factory=dict)
    total_tokens_estimated: int = Field(default=0, ge=0)
    token_limit: int = Field(default=4096, ge=100)
    is_truncated: bool = Field(default=False)
    summary_of_truncated: str | None = None


class ContextBuilderConfig(BaseModel):
    """Configuration for context builder."""

    model_config = ConfigDict(extra="forbid")

    max_context_tokens: int = Field(default=4096, ge=100, le=200000)
    min_context_tokens: int = Field(default=512, ge=100)
    max_recent_messages: int = Field(default=20, ge=1)
    min_messages_to_keep: int = Field(default=2, ge=1)
    average_tokens_per_message: float = Field(default=150.0, ge=50.0)
    include_metadata: bool = Field(default=False)
    summarize_truncated: bool = Field(default=True)


class ContextBuilderError(Exception):
    """Base exception for context builder errors."""

    pass


class InvalidContextError(ContextBuilderError):
    """Raised when context is invalid."""

    pass


class ContextBuilder:
    """Builds conversation context for LLM requests from session memory.

    Orchestrates context construction from interaction history including:
    - Recent message retrieval
    - Context window management
    - Token limit handling
    - Message summarization
    - LLM-specific formatting

    Architecture:
    - Integrates with SessionMemory for interaction history
    - Manages token limits for Claude/Bedrock compatibility
    - Supports context truncation and summarization
    - Formats context for LLM prompts
    - Tracks metadata for context decisions
    """

    # Tokens per character estimate (conservative for LLM counting)
    TOKENS_PER_CHARACTER = 0.25

    def __init__(
        self,
        session_memory: SessionMemoryManager,
        config: ContextBuilderConfig | None = None,
    ) -> None:
        """Initialize context builder.

        Args:
            session_memory: SessionMemoryManager instance
            config: Optional custom configuration
        """
        self._session_memory = session_memory
        self._config = config or ContextBuilderConfig()
        self._logger = logger

        self._logger.info(
            "ContextBuilder initialized",
            extra={
                "session_id": str(session_memory._session_id),
                "max_tokens": self._config.max_context_tokens,
                "max_messages": self._config.max_recent_messages,
            },
        )

    def build_context(
        self,
        include_system_context: bool = True,
        include_metadata: bool | None = None,
    ) -> ConversationContext:
        """Build complete conversation context for LLM.

        Retrieves recent interactions from session memory, formats them
        for LLM consumption, and manages token limits.

        Args:
            include_system_context: Include session-level system context
            include_metadata: Override config for metadata inclusion

        Returns:
            ConversationContext ready for LLM

        Raises:
            ContextBuilderError: If context building fails
        """
        self._logger.debug(
            "Building conversation context",
            extra={
                "session_id": str(self._session_memory._session_id),
                "include_system": include_system_context,
            },
        )

        try:
            session_memory = self._session_memory.get_memory_state()

            # Get recent interactions
            recent_interactions = self.get_recent_messages(
                limit=self._config.max_recent_messages
            )

            # Convert to context messages
            context_messages = self._interactions_to_context_messages(
                recent_interactions,
                include_metadata=include_metadata
                or self._config.include_metadata,
            )

            # Build system context
            system_context = None
            if include_system_context:
                system_context = self._build_system_context(session_memory)

            # Create context
            context = ConversationContext(
                session_id=self._session_memory._session_id,
                user_id=self._session_memory._user_id,
                messages=context_messages,
                system_context=system_context,
                token_limit=self._config.max_context_tokens,
            )

            # Estimate tokens
            context.total_tokens_estimated = self._estimate_tokens(context)

            # Truncate if necessary
            if context.total_tokens_estimated > self._config.max_context_tokens:
                self._logger.debug(
                    "Context exceeds token limit, truncating",
                    extra={
                        "estimated_tokens": context.total_tokens_estimated,
                        "limit": self._config.max_context_tokens,
                    },
                )
                context = self.truncate_context(context)

            self._logger.debug(
                "Context built successfully",
                extra={
                    "messages": len(context.messages),
                    "tokens": context.total_tokens_estimated,
                    "truncated": context.is_truncated,
                },
            )

            return context

        except Exception as exc:
            self._logger.error(
                "Context building failed",
                extra={
                    "session_id": str(self._session_memory._session_id),
                    "error": str(exc),
                },
            )
            raise ContextBuilderError(f"Failed to build context: {str(exc)}") from exc

    def get_recent_messages(
        self,
        limit: int | None = None,
    ) -> list[InteractionLog]:
        """Get recent interaction messages from session memory.

        Args:
            limit: Maximum number of messages to retrieve

        Returns:
            List of recent InteractionLog entries

        Raises:
            ContextBuilderError: If retrieval fails
        """
        limit = limit or self._config.max_recent_messages

        self._logger.debug(
            "Retrieving recent messages",
            extra={"session_id": str(self._session_memory._session_id), "limit": limit},
        )

        try:
            interactions = self._session_memory.get_recent_interactions(limit=limit)

            self._logger.debug(
                "Messages retrieved",
                extra={
                    "session_id": str(self._session_memory._session_id),
                    "count": len(interactions),
                },
            )

            return interactions

        except Exception as exc:
            self._logger.error(
                "Message retrieval failed",
                extra={"error": str(exc)},
            )
            raise ContextBuilderError(
                f"Failed to retrieve messages: {str(exc)}"
            ) from exc

    def truncate_context(
        self,
        context: ConversationContext,
        preserve_recent_ratio: float = 0.7,
    ) -> ConversationContext:
        """Truncate context to fit within token limits.

        Strategy:
        1. Keep system context (never truncated)
        2. Keep most recent messages (preserve_recent_ratio)
        3. Summarize older messages if enabled
        4. Remove oldest messages if necessary

        Args:
            context: Context to truncate
            preserve_recent_ratio: Ratio of recent messages to preserve (0-1)

        Returns:
            Truncated ConversationContext

        Raises:
            InvalidContextError: If context is invalid
        """
        self._logger.info(
            "Truncating context",
            extra={
                "session_id": str(context.session_id),
                "current_tokens": context.total_tokens_estimated,
                "limit": context.token_limit,
            },
        )

        try:
            if not context.messages:
                return context

            truncated_context = context.model_copy()
            target_tokens = int(self._config.max_context_tokens * 0.9)

            # Ensure minimum messages preserved
            num_recent = max(
                int(len(context.messages) * preserve_recent_ratio),
                self._config.min_messages_to_keep,
            )

            if len(context.messages) <= num_recent:
                self._logger.debug(
                    "Context within acceptable limits after ratio check",
                    extra={"messages": len(context.messages)},
                )
                return truncated_context

            # Separate recent and older messages
            older_messages = context.messages[:-num_recent]
            recent_messages = context.messages[-num_recent:]

            # Try summarizing older messages
            if self._config.summarize_truncated and older_messages:
                summary = self._summarize_messages(older_messages)
                truncated_context.summary_of_truncated = summary

                self._logger.debug(
                    "Older messages summarized",
                    extra={
                        "older_count": len(older_messages),
                        "summary_length": len(summary),
                    },
                )

            # Use only recent messages
            truncated_context.messages = recent_messages
            truncated_context.total_tokens_estimated = self._estimate_tokens(
                truncated_context
            )
            truncated_context.is_truncated = True

            self._logger.info(
                "Context truncated successfully",
                extra={
                    "original_messages": len(context.messages),
                    "truncated_messages": len(truncated_context.messages),
                    "final_tokens": truncated_context.total_tokens_estimated,
                    "has_summary": truncated_context.summary_of_truncated is not None,
                },
            )

            return truncated_context

        except Exception as exc:
            self._logger.error(
                "Context truncation failed",
                extra={"error": str(exc)},
            )
            raise InvalidContextError(f"Failed to truncate context: {str(exc)}") from exc

    def format_for_llm(
        self,
        context: ConversationContext,
        include_timestamps: bool = False,
    ) -> str:
        """Format context as string suitable for LLM prompt.

        Args:
            context: ConversationContext to format
            include_timestamps: Include message timestamps

        Returns:
            Formatted context string

        Raises:
            InvalidContextError: If formatting fails
        """
        self._logger.debug(
            "Formatting context for LLM",
            extra={
                "session_id": str(context.session_id),
                "messages": len(context.messages),
            },
        )

        try:
            lines = []

            # Add system context if present
            if context.system_context:
                lines.append("SYSTEM CONTEXT:")
                lines.append(context.system_context)
                lines.append("")

            # Add truncation notice and summary
            if context.is_truncated and context.summary_of_truncated:
                lines.append("CONVERSATION SUMMARY (earlier messages):")
                lines.append(context.summary_of_truncated)
                lines.append("")

            # Add conversation history
            if context.messages:
                lines.append("CONVERSATION HISTORY:")
                for msg in context.messages:
                    role_label = msg.role.value.upper()
                    timestamp_str = ""
                    if include_timestamps and msg.timestamp:
                        timestamp_str = f" [{msg.timestamp.isoformat()}]"

                    lines.append(f"{role_label}{timestamp_str}:")
                    lines.append(msg.content)
                    lines.append("")

            formatted = "\n".join(lines)

            self._logger.debug(
                "Context formatted for LLM",
                extra={
                    "session_id": str(context.session_id),
                    "length": len(formatted),
                },
            )

            return formatted

        except Exception as exc:
            self._logger.error(
                "LLM formatting failed",
                extra={"error": str(exc)},
            )
            raise InvalidContextError(f"Failed to format context: {str(exc)}") from exc

    def get_message_summary(self) -> str:
        """Get high-level summary of session interaction history.

        Returns:
            Formatted summary string
        """
        return self._session_memory.get_interaction_summary()

    def _interactions_to_context_messages(
        self,
        interactions: list[InteractionLog],
        include_metadata: bool = False,
    ) -> list[ContextMessage]:
        """Convert InteractionLog entries to ContextMessage format.

        Args:
            interactions: List of InteractionLog entries
            include_metadata: Include metadata in messages

        Returns:
            List of ContextMessage objects
        """
        messages = []

        for interaction in interactions:
            # User message
            user_msg = ContextMessage(
                role=ContextRole.USER,
                content=interaction.user_input,
                timestamp=interaction.timestamp,
                metadata=interaction.metadata if include_metadata else {},
            )
            messages.append(user_msg)

            # Assistant message
            assistant_msg = ContextMessage(
                role=ContextRole.ASSISTANT,
                content=interaction.assistant_response,
                timestamp=interaction.timestamp,
                metadata={"type": interaction.interaction_type}
                if include_metadata
                else {},
            )
            messages.append(assistant_msg)

        return messages

    def _build_system_context(self, session_memory: Any) -> str:
        """Build system context from session memory.

        Args:
            session_memory: SessionMemory object

        Returns:
            Formatted system context string
        """
        context_parts = []

        # Session metadata
        context_parts.append("SESSION CONTEXT:")

        if session_memory.current_category:
            context_parts.append(f"- Category: {session_memory.current_category}")

        if session_memory.current_urgency.level != "NORMAL":
            context_parts.append(
                f"- Urgency: {session_memory.current_urgency.level}"
            )

        if session_memory.active_filters:
            filters_str = ", ".join(
                f"{k}={v}" for k, v in session_memory.active_filters.items()
            )
            context_parts.append(f"- Filters: {filters_str}")

        if session_memory.cart_snapshots:
            latest_cart = session_memory.cart_snapshots[-1]
            context_parts.append(
                f"- Cart: {latest_cart.items_count} items, ${latest_cart.total_amount:.2f}"
            )

        return "\n".join(context_parts)

    def _estimate_tokens(self, context: ConversationContext) -> int:
        """Estimate token count for context.

        Uses conservative approximation: characters * TOKENS_PER_CHARACTER
        For Claude models, typically ~4-5 characters per token.

        Args:
            context: ConversationContext to estimate

        Returns:
            Estimated token count

        Note:
            Future: Integrate with actual tokenizer for precise counts.
            Claude tokenizer API can be used for exact token calculation.
        """
        token_count = 0

        # System context
        if context.system_context:
            token_count += int(len(context.system_context) * self.TOKENS_PER_CHARACTER)

        # Messages
        for msg in context.messages:
            token_count += int(len(msg.content) * self.TOKENS_PER_CHARACTER)

        # Summary
        if context.summary_of_truncated:
            token_count += int(
                len(context.summary_of_truncated) * self.TOKENS_PER_CHARACTER
            )

        # Add overhead for formatting
        token_count = int(token_count * 1.1)

        return token_count

    def _summarize_messages(self, messages: list[ContextMessage]) -> str:
        """Generate summary of message list for truncation.

        Args:
            messages: Messages to summarize

        Returns:
            Summary text

        Note:
            Future: Integrate with Bedrock Claude for intelligent summarization.
            Could use lightweight model or extractive summarization.
        """
        if not messages:
            return "No previous messages."

        user_messages = [m for m in messages if m.role == ContextRole.USER]
        topics = []

        for msg in user_messages[:5]:
            first_sentence = msg.content.split(".")[0]
            if len(first_sentence) > 100:
                first_sentence = first_sentence[:100] + "..."
            topics.append(first_sentence)

        if topics:
            return f"Earlier in conversation: {'; '.join(topics)}"

        return f"Previous conversation with {len(messages)} messages."

    def get_context_stats(
        self,
        context: ConversationContext,
    ) -> dict[str, Any]:
        """Get statistics about current context.

        Args:
            context: Context to analyze

        Returns:
            Dictionary with context statistics
        """
        user_messages = [m for m in context.messages if m.role == ContextRole.USER]
        assistant_messages = [
            m for m in context.messages if m.role == ContextRole.ASSISTANT
        ]

        avg_user_length = (
            sum(len(m.content) for m in user_messages) / len(user_messages)
            if user_messages
            else 0
        )

        avg_assistant_length = (
            sum(len(m.content) for m in assistant_messages) / len(assistant_messages)
            if assistant_messages
            else 0
        )

        return {
            "total_messages": len(context.messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "estimated_tokens": context.total_tokens_estimated,
            "token_limit": context.token_limit,
            "token_utilization_percent": round(
                (context.total_tokens_estimated / context.token_limit) * 100, 1
            ),
            "avg_user_message_length": round(avg_user_length),
            "avg_assistant_message_length": round(avg_assistant_length),
            "is_truncated": context.is_truncated,
            "has_system_context": context.system_context is not None,
            "has_summary": context.summary_of_truncated is not None,
        }
