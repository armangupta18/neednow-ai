"""Text chunking module.

Splits text into semantically meaningful chunks suitable for
embedding generation and vector storage.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TextChunk:
    """A single chunk produced by the chunker."""

    text: str
    index: int = 0
    start_char: int = 0
    end_char: int = 0
    metadata: dict[str, str] = field(default_factory=dict)


class TextChunker:
    """Splits text into overlapping fixed-size chunks.

    Uses a sliding window approach with configurable chunk size and
    overlap to maintain contextual continuity across boundaries.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        separator: str = "\n",
    ) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator

    def chunk(self, text: str, *, metadata: dict[str, str] | None = None) -> list[TextChunk]:
        """Split text into chunks.

        Args:
            text: The input text to chunk.
            metadata: Optional metadata attached to every chunk.

        Returns:
            Ordered list of TextChunk objects.
        """
        if not text.strip():
            return []

        chunks: list[TextChunk] = []
        step = self.chunk_size - self.chunk_overlap
        start = 0
        index = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    TextChunk(
                        text=chunk_text,
                        index=index,
                        start_char=start,
                        end_char=end,
                        metadata=metadata or {},
                    )
                )
                index += 1

            if end >= len(text):
                break
            start += step

        return chunks

    def chunk_by_separator(
        self, text: str, *, metadata: dict[str, str] | None = None
    ) -> list[TextChunk]:
        """Split text by the configured separator, respecting chunk_size limits."""
        segments = text.split(self.separator)
        chunks: list[TextChunk] = []
        current_text = ""
        current_start = 0
        index = 0

        for segment in segments:
            candidate = (
                f"{current_text}{self.separator}{segment}" if current_text else segment
            )
            if len(candidate) > self.chunk_size and current_text:
                chunks.append(
                    TextChunk(
                        text=current_text.strip(),
                        index=index,
                        start_char=current_start,
                        end_char=current_start + len(current_text),
                        metadata=metadata or {},
                    )
                )
                index += 1
                current_start += len(current_text) + len(self.separator)
                current_text = segment
            else:
                current_text = candidate

        if current_text.strip():
            chunks.append(
                TextChunk(
                    text=current_text.strip(),
                    index=index,
                    start_char=current_start,
                    end_char=current_start + len(current_text),
                    metadata=metadata or {},
                )
            )

        return chunks
