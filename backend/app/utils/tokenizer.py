"""Text tokenization utilities for NeedNow AI.

Provides token counting, estimation, text chunking, and context window
management for Bedrock Claude integration, memory engine, and prompt
management. Uses a lightweight heuristic tokenizer — no external
tokenizer dependency required.

Architecture:
    - Bedrock Claude Integration: Token budget enforcement for prompts.
    - Memory Engine: Chunking memory content for embedding pipelines.
    - Prompt Management: Ensuring prompts fit within model context windows.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Claude model context windows (tokens)
MODEL_CONTEXT_WINDOWS: dict[str, int] = {
    "anthropic.claude-3-sonnet": 200_000,
    "anthropic.claude-3-haiku": 200_000,
    "anthropic.claude-3-opus": 200_000,
    "anthropic.claude-v2": 100_000,
    "anthropic.claude-instant-v1": 100_000,
    "amazon.titan-text-express-v1": 8_192,
    "amazon.titan-text-lite-v1": 4_096,
    "default": 100_000,
}

# Average characters per token for Claude models (empirically ~3.5–4.0)
DEFAULT_CHARS_PER_TOKEN: float = 3.8


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class TokenCount:
    """Result of a token counting operation."""

    token_count: int
    char_count: int
    word_count: int
    estimated: bool = True


@dataclass
class ChunkResult:
    """Result of a text chunking operation."""

    chunks: list[str]
    total_chunks: int
    avg_tokens_per_chunk: int
    total_tokens: int


@dataclass
class TruncateResult:
    """Result of a text truncation operation."""

    text: str
    original_tokens: int
    truncated_tokens: int
    was_truncated: bool


# ---------------------------------------------------------------------------
# TextTokenizer
# ---------------------------------------------------------------------------


class TextTokenizer:
    """Lightweight text tokenizer for LLM prompt management.

    Provides token counting, estimation, text chunking, and context
    window validation without requiring external tokenizer libraries.
    Uses a character-ratio heuristic calibrated for Claude models.

    Args:
        model_id: Bedrock model identifier (used for context window lookup).
        chars_per_token: Character-to-token ratio for estimation.
        default_max_tokens: Fallback context window size.
    """

    # Regex patterns for tokenization heuristic
    _WORD_PATTERN = re.compile(r"\S+")
    _SUBWORD_PATTERN = re.compile(
        r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)|[0-9]+|[^\w\s]|\s+"
    )
    _WHITESPACE_PATTERN = re.compile(r"\s+")
    _SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")
    _PARAGRAPH_PATTERN = re.compile(r"\n\s*\n")

    def __init__(
        self,
        model_id: str = "anthropic.claude-3-sonnet",
        chars_per_token: float = DEFAULT_CHARS_PER_TOKEN,
        default_max_tokens: int | None = None,
    ) -> None:
        self.model_id = model_id
        self.chars_per_token = chars_per_token
        self.default_max_tokens = default_max_tokens or MODEL_CONTEXT_WINDOWS.get(
            model_id, MODEL_CONTEXT_WINDOWS["default"]
        )

        logger.debug(
            "TextTokenizer initialized: model=%s, chars_per_token=%.1f, max_tokens=%d",
            model_id,
            chars_per_token,
            self.default_max_tokens,
        )

    # ------------------------------------------------------------------
    # Token Counting
    # ------------------------------------------------------------------

    def count_tokens(self, text: str) -> TokenCount:
        """Count the estimated number of tokens in text.

        Uses a subword-level heuristic that approximates BPE tokenization
        by counting word boundaries, punctuation, and numeric sequences.
        More accurate than pure character division.

        Args:
            text: Input text to count.

        Returns:
            TokenCount with estimated token, character, and word counts.
        """
        if not text:
            return TokenCount(token_count=0, char_count=0, word_count=0)

        char_count = len(text)
        word_count = len(self._WORD_PATTERN.findall(text))

        # Subword heuristic: split on subword boundaries
        subwords = self._SUBWORD_PATTERN.findall(text)
        # Filter whitespace-only tokens (they're typically merged in BPE)
        meaningful_subwords = [
            sw for sw in subwords if sw.strip() or sw == " "
        ]

        # Approximate: each meaningful subword ~ 1 token,
        # but merge short adjacent subwords
        token_estimate = self._merge_estimate(meaningful_subwords)

        # Cross-validate with character ratio
        char_estimate = max(1, int(char_count / self.chars_per_token))

        # Weighted average favoring subword heuristic
        final_estimate = int(token_estimate * 0.6 + char_estimate * 0.4)
        final_estimate = max(1, final_estimate)

        logger.debug(
            "count_tokens: chars=%d, words=%d, tokens≈%d (subword=%d, char_ratio=%d)",
            char_count,
            word_count,
            final_estimate,
            token_estimate,
            char_estimate,
        )

        return TokenCount(
            token_count=final_estimate,
            char_count=char_count,
            word_count=word_count,
            estimated=True,
        )

    def estimate_tokens(self, text: str) -> int:
        """Quick token estimate using character ratio.

        Faster than count_tokens() — suitable for budget checks where
        exact accuracy is less critical.

        Args:
            text: Input text.

        Returns:
            Estimated token count.
        """
        if not text:
            return 0
        estimate = max(1, int(len(text) / self.chars_per_token))
        return estimate

    # ------------------------------------------------------------------
    # Text Chunking
    # ------------------------------------------------------------------

    def chunk_text(
        self,
        text: str,
        max_tokens_per_chunk: int = 512,
        *,
        overlap_tokens: int = 50,
        strategy: str = "sentence",
    ) -> ChunkResult:
        """Split text into chunks that fit within a token budget.

        Supports multiple splitting strategies to maintain semantic
        coherence within each chunk.

        Args:
            text: Input text to chunk.
            max_tokens_per_chunk: Maximum tokens per chunk.
            overlap_tokens: Token overlap between adjacent chunks.
            strategy: Splitting strategy — "sentence", "paragraph", or "word".

        Returns:
            ChunkResult with chunks and metadata.
        """
        if not text.strip():
            return ChunkResult(chunks=[], total_chunks=0, avg_tokens_per_chunk=0, total_tokens=0)

        total_tokens = self.estimate_tokens(text)

        # If text fits in a single chunk, return as-is
        if total_tokens <= max_tokens_per_chunk:
            return ChunkResult(
                chunks=[text],
                total_chunks=1,
                avg_tokens_per_chunk=total_tokens,
                total_tokens=total_tokens,
            )

        # Choose splitting strategy
        if strategy == "paragraph":
            chunks = self._chunk_by_paragraphs(text, max_tokens_per_chunk, overlap_tokens)
        elif strategy == "sentence":
            chunks = self._chunk_by_sentences(text, max_tokens_per_chunk, overlap_tokens)
        else:
            chunks = self._chunk_by_words(text, max_tokens_per_chunk, overlap_tokens)

        # Filter empty chunks
        chunks = [c.strip() for c in chunks if c.strip()]

        # Compute metrics
        chunk_tokens = [self.estimate_tokens(c) for c in chunks]
        avg_tokens = int(sum(chunk_tokens) / len(chunk_tokens)) if chunks else 0

        logger.debug(
            "chunk_text: strategy=%s, total_tokens=%d, chunks=%d, avg_tokens=%d",
            strategy,
            total_tokens,
            len(chunks),
            avg_tokens,
        )

        return ChunkResult(
            chunks=chunks,
            total_chunks=len(chunks),
            avg_tokens_per_chunk=avg_tokens,
            total_tokens=total_tokens,
        )

    # ------------------------------------------------------------------
    # Text Truncation
    # ------------------------------------------------------------------

    def truncate_text(
        self,
        text: str,
        max_tokens: int | None = None,
        *,
        suffix: str = "...",
        preserve_words: bool = True,
    ) -> TruncateResult:
        """Safely truncate text to fit within a token budget.

        Attempts to truncate at word or sentence boundaries to
        maintain readability.

        Args:
            text: Input text.
            max_tokens: Token limit (defaults to model context window).
            suffix: String appended when text is truncated.
            preserve_words: If True, truncate at word boundaries.

        Returns:
            TruncateResult with truncated text and metadata.
        """
        limit = max_tokens or self.default_max_tokens
        original_tokens = self.estimate_tokens(text)

        if original_tokens <= limit:
            return TruncateResult(
                text=text,
                original_tokens=original_tokens,
                truncated_tokens=original_tokens,
                was_truncated=False,
            )

        # Calculate character budget
        suffix_tokens = self.estimate_tokens(suffix)
        available_tokens = limit - suffix_tokens
        max_chars = int(available_tokens * self.chars_per_token)

        if preserve_words:
            truncated = self._truncate_at_word_boundary(text, max_chars)
        else:
            truncated = text[:max_chars]

        truncated = truncated.rstrip() + suffix
        truncated_tokens = self.estimate_tokens(truncated)

        logger.debug(
            "truncate_text: original=%d tokens, truncated=%d tokens, limit=%d",
            original_tokens,
            truncated_tokens,
            limit,
        )

        return TruncateResult(
            text=truncated,
            original_tokens=original_tokens,
            truncated_tokens=truncated_tokens,
            was_truncated=True,
        )

    # ------------------------------------------------------------------
    # Context Window Validation
    # ------------------------------------------------------------------

    def within_limit(
        self,
        text: str,
        max_tokens: int | None = None,
        *,
        reserve_tokens: int = 0,
    ) -> bool:
        """Check whether text fits within the context window.

        Args:
            text: Input text to check.
            max_tokens: Token limit (defaults to model context window).
            reserve_tokens: Tokens to reserve for response generation.

        Returns:
            True if text fits within the available budget.
        """
        limit = max_tokens or self.default_max_tokens
        available = limit - reserve_tokens
        token_count = self.estimate_tokens(text)

        fits = token_count <= available

        if not fits:
            logger.warning(
                "Text exceeds context window: %d tokens > %d available "
                "(limit=%d, reserved=%d)",
                token_count,
                available,
                limit,
                reserve_tokens,
            )

        return fits

    def remaining_budget(
        self,
        consumed_text: str,
        max_tokens: int | None = None,
        *,
        reserve_tokens: int = 0,
    ) -> int:
        """Calculate remaining token budget after consuming text.

        Args:
            consumed_text: Text already using budget.
            max_tokens: Total token limit.
            reserve_tokens: Tokens reserved for response.

        Returns:
            Number of tokens remaining (may be negative if over budget).
        """
        limit = max_tokens or self.default_max_tokens
        consumed = self.estimate_tokens(consumed_text)
        return limit - consumed - reserve_tokens

    # ------------------------------------------------------------------
    # Utility Methods
    # ------------------------------------------------------------------

    def get_context_window(self, model_id: str | None = None) -> int:
        """Get the context window size for a model.

        Args:
            model_id: Bedrock model identifier. Defaults to instance model.

        Returns:
            Maximum context window in tokens.
        """
        mid = model_id or self.model_id
        return MODEL_CONTEXT_WINDOWS.get(mid, MODEL_CONTEXT_WINDOWS["default"])

    def token_to_char_estimate(self, tokens: int) -> int:
        """Convert a token count to an approximate character count.

        Args:
            tokens: Number of tokens.

        Returns:
            Estimated character count.
        """
        return int(tokens * self.chars_per_token)

    # ------------------------------------------------------------------
    # Private Chunking Implementations
    # ------------------------------------------------------------------

    def _chunk_by_sentences(
        self,
        text: str,
        max_tokens: int,
        overlap_tokens: int,
    ) -> list[str]:
        """Split text into chunks at sentence boundaries."""
        sentences = self._SENTENCE_PATTERN.split(text)
        return self._assemble_chunks(sentences, max_tokens, overlap_tokens)

    def _chunk_by_paragraphs(
        self,
        text: str,
        max_tokens: int,
        overlap_tokens: int,
    ) -> list[str]:
        """Split text into chunks at paragraph boundaries."""
        paragraphs = self._PARAGRAPH_PATTERN.split(text)
        return self._assemble_chunks(paragraphs, max_tokens, overlap_tokens)

    def _chunk_by_words(
        self,
        text: str,
        max_tokens: int,
        overlap_tokens: int,
    ) -> list[str]:
        """Split text into chunks at word boundaries."""
        words = text.split()
        max_chars = int(max_tokens * self.chars_per_token)
        overlap_chars = int(overlap_tokens * self.chars_per_token)
        step = max(1, max_chars - overlap_chars)

        chunks: list[str] = []
        current = ""

        for word in words:
            candidate = f"{current} {word}".strip() if current else word
            if len(candidate) > max_chars and current:
                chunks.append(current)
                # Overlap: start next chunk with tail of current
                overlap_start = max(0, len(current) - overlap_chars)
                current = current[overlap_start:].strip() + " " + word
                current = current.strip()
            else:
                current = candidate

        if current.strip():
            chunks.append(current.strip())

        return chunks

    def _assemble_chunks(
        self,
        segments: list[str],
        max_tokens: int,
        overlap_tokens: int,
    ) -> list[str]:
        """Assemble segments into chunks respecting token limits."""
        max_chars = int(max_tokens * self.chars_per_token)
        overlap_chars = int(overlap_tokens * self.chars_per_token)

        chunks: list[str] = []
        current = ""

        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue

            candidate = f"{current} {segment}".strip() if current else segment

            if len(candidate) > max_chars and current:
                chunks.append(current.strip())
                # Overlap: carry tail of current chunk
                if overlap_chars > 0:
                    tail = current[-overlap_chars:].strip()
                    current = f"{tail} {segment}".strip()
                else:
                    current = segment
            else:
                current = candidate

        if current.strip():
            chunks.append(current.strip())

        return chunks

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _merge_estimate(self, subwords: list[str]) -> int:
        """Estimate token count by merging short adjacent subwords."""
        if not subwords:
            return 0

        count = 0
        buffer_len = 0

        for sw in subwords:
            sw_len = len(sw)
            if sw_len <= 2 and buffer_len < 4:
                # Short subword — may be merged with neighbors
                buffer_len += sw_len
            else:
                if buffer_len > 0:
                    count += 1
                    buffer_len = 0
                count += 1

        if buffer_len > 0:
            count += 1

        return count

    @staticmethod
    def _truncate_at_word_boundary(text: str, max_chars: int) -> str:
        """Truncate text at the nearest word boundary before max_chars."""
        if len(text) <= max_chars:
            return text

        truncated = text[:max_chars]
        # Find the last space to avoid cutting a word
        last_space = truncated.rfind(" ")
        if last_space > max_chars * 0.5:
            return truncated[:last_space]
        return truncated
