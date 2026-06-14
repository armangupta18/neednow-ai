"""General helper utilities for NeedNow AI.

Provides shared utility functions for UUID generation, timestamps,
safe dictionary operations, environment access, and async retry logic.
Used across all layers of the platform.

Responsibilities:
    - Generate UUIDs and unique identifiers.
    - Generate and format timestamps.
    - Safe dictionary access and merging.
    - Environment variable helpers with type coercion.
    - Async retry with configurable backoff.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, TypeVar, overload
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ---------------------------------------------------------------------------
# HelperUtils
# ---------------------------------------------------------------------------


class HelperUtils:
    """Collection of general-purpose helper utilities.

    All methods are static for easy use without instantiation.
    Designed for reuse across services, agents, workers, and API layers.
    """

    # ------------------------------------------------------------------
    # UUID Generation
    # ------------------------------------------------------------------

    @staticmethod
    def generate_uuid() -> UUID:
        """Generate a new UUID v4.

        Returns:
            A new random UUID.
        """
        return uuid4()

    @staticmethod
    def generate_uuid_str() -> str:
        """Generate a new UUID v4 as a string.

        Returns:
            UUID string (e.g., "a1b2c3d4-e5f6-...").
        """
        return str(uuid4())

    @staticmethod
    def generate_short_id(length: int = 12) -> str:
        """Generate a short unique identifier (hex substring of UUID).

        Args:
            length: Character count (max 32).

        Returns:
            Short hex string (e.g., "a1b2c3d4e5f6").
        """
        return uuid4().hex[:length]

    # ------------------------------------------------------------------
    # Timestamp Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def current_timestamp() -> datetime:
        """Return the current UTC datetime (timezone-aware).

        Returns:
            datetime with UTC timezone.
        """
        return datetime.now(timezone.utc)

    @staticmethod
    def current_timestamp_iso() -> str:
        """Return the current UTC datetime as ISO 8601 string.

        Returns:
            ISO formatted timestamp string.
        """
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def timestamp_epoch() -> float:
        """Return the current time as a Unix epoch float.

        Returns:
            Seconds since epoch.
        """
        return time.time()

    @staticmethod
    def timestamp_ms() -> int:
        """Return the current time as milliseconds since epoch.

        Returns:
            Integer milliseconds.
        """
        return int(time.time() * 1000)

    @staticmethod
    def format_timestamp(
        dt: datetime | None,
        fmt: str = "%Y-%m-%d %H:%M:%S UTC",
    ) -> str | None:
        """Format a datetime for display.

        Args:
            dt: Datetime to format (returns None if dt is None).
            fmt: strftime format string.

        Returns:
            Formatted string or None.
        """
        if dt is None:
            return None
        return dt.strftime(fmt)

    @staticmethod
    def time_ago(dt: datetime) -> str:
        """Return a human-readable 'time ago' string.

        Args:
            dt: Past datetime to compare against now.

        Returns:
            String like "5 minutes ago", "2 hours ago", "3 days ago".
        """
        delta = datetime.now(timezone.utc) - dt
        seconds = int(delta.total_seconds())

        if seconds < 60:
            return f"{seconds} seconds ago"
        if seconds < 3600:
            return f"{seconds // 60} minutes ago"
        if seconds < 86400:
            return f"{seconds // 3600} hours ago"
        return f"{seconds // 86400} days ago"

    # ------------------------------------------------------------------
    # Safe Dictionary Operations
    # ------------------------------------------------------------------

    @staticmethod
    def safe_get(
        data: dict[str, Any] | None,
        *keys: str,
        default: Any = None,
    ) -> Any:
        """Safely access nested dictionary keys.

        Traverses a chain of keys without raising KeyError or TypeError.

        Args:
            data: Root dictionary (may be None).
            *keys: Sequence of keys to traverse.
            default: Value to return if any key is missing.

        Returns:
            The value at the nested path, or default.

        Examples:
            >>> HelperUtils.safe_get({"a": {"b": {"c": 1}}}, "a", "b", "c")
            1
            >>> HelperUtils.safe_get({"a": 1}, "x", "y", default="missing")
            'missing'
        """
        current: Any = data
        for key in keys:
            if current is None:
                return default
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return default
        return current if current is not None else default

    @staticmethod
    def merge_dicts(
        base: dict[str, Any],
        override: dict[str, Any],
        *,
        deep: bool = True,
    ) -> dict[str, Any]:
        """Merge two dictionaries with optional deep merging.

        Args:
            base: Base dictionary (not mutated).
            override: Dictionary whose values take precedence.
            deep: If True, recursively merge nested dicts.
                If False, override replaces nested dicts entirely.

        Returns:
            New merged dictionary.

        Examples:
            >>> HelperUtils.merge_dicts({"a": 1, "b": {"x": 1}}, {"b": {"y": 2}})
            {'a': 1, 'b': {'x': 1, 'y': 2}}
        """
        result = dict(base)

        for key, value in override.items():
            if (
                deep
                and key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = HelperUtils.merge_dicts(result[key], value, deep=True)
            else:
                result[key] = value

        return result

    @staticmethod
    def pick(data: dict[str, Any], keys: list[str]) -> dict[str, Any]:
        """Extract a subset of keys from a dictionary.

        Args:
            data: Source dictionary.
            keys: Keys to include.

        Returns:
            New dict with only the specified keys.
        """
        return {k: data[k] for k in keys if k in data}

    @staticmethod
    def omit(data: dict[str, Any], keys: list[str]) -> dict[str, Any]:
        """Return a dictionary without the specified keys.

        Args:
            data: Source dictionary.
            keys: Keys to exclude.

        Returns:
            New dict without the excluded keys.
        """
        exclude = set(keys)
        return {k: v for k, v in data.items() if k not in exclude}

    # ------------------------------------------------------------------
    # Environment Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def get_env(key: str, default: str = "") -> str:
        """Get an environment variable with a default.

        Args:
            key: Environment variable name.
            default: Fallback value.

        Returns:
            Environment variable value or default.
        """
        return os.environ.get(key, default)

    @staticmethod
    def get_env_int(key: str, default: int = 0) -> int:
        """Get an environment variable as an integer.

        Args:
            key: Environment variable name.
            default: Fallback value.

        Returns:
            Parsed integer or default.
        """
        raw = os.environ.get(key)
        if raw is None:
            return default
        try:
            return int(raw)
        except ValueError:
            logger.warning(
                "Environment variable '%s' is not a valid integer: '%s'", key, raw
            )
            return default

    @staticmethod
    def get_env_float(key: str, default: float = 0.0) -> float:
        """Get an environment variable as a float.

        Args:
            key: Environment variable name.
            default: Fallback value.

        Returns:
            Parsed float or default.
        """
        raw = os.environ.get(key)
        if raw is None:
            return default
        try:
            return float(raw)
        except ValueError:
            logger.warning(
                "Environment variable '%s' is not a valid float: '%s'", key, raw
            )
            return default

    @staticmethod
    def get_env_bool(key: str, default: bool = False) -> bool:
        """Get an environment variable as a boolean.

        Truthy values: "1", "true", "yes", "on" (case-insensitive).

        Args:
            key: Environment variable name.
            default: Fallback value.

        Returns:
            Boolean value.
        """
        raw = os.environ.get(key)
        if raw is None:
            return default
        return raw.strip().lower() in ("1", "true", "yes", "on")

    @staticmethod
    def get_env_list(key: str, separator: str = ",", default: list[str] | None = None) -> list[str]:
        """Get an environment variable as a list of strings.

        Args:
            key: Environment variable name.
            separator: Delimiter for splitting.
            default: Fallback list.

        Returns:
            List of stripped, non-empty strings.
        """
        raw = os.environ.get(key)
        if raw is None:
            return default or []
        return [item.strip() for item in raw.split(separator) if item.strip()]

    # ------------------------------------------------------------------
    # Retry Helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def retry_async(
        fn: Callable[..., Awaitable[T]],
        *args: Any,
        max_retries: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        max_delay: float = 30.0,
        exceptions: tuple[type[Exception], ...] = (Exception,),
        on_retry: Callable[[int, Exception], None] | None = None,
        **kwargs: Any,
    ) -> T:
        """Retry an async function with configurable exponential backoff.

        Args:
            fn: Async callable to retry.
            *args: Positional arguments for fn.
            max_retries: Maximum number of retry attempts.
            delay: Initial delay between retries (seconds).
            backoff: Multiplier applied to delay on each retry.
            max_delay: Maximum delay cap (seconds).
            exceptions: Tuple of exception types to retry on.
            on_retry: Optional callback invoked on each retry (attempt, exception).
            **kwargs: Keyword arguments for fn.

        Returns:
            Result of the successful call.

        Raises:
            The last exception if all retries are exhausted.
        """
        last_exception: Exception | None = None
        current_delay = delay

        for attempt in range(max_retries + 1):
            try:
                result = await fn(*args, **kwargs)
                if attempt > 0:
                    logger.info(
                        "retry_async succeeded on attempt %d/%d for %s",
                        attempt + 1,
                        max_retries + 1,
                        fn.__name__,
                    )
                return result

            except exceptions as exc:
                last_exception = exc

                if attempt >= max_retries:
                    logger.error(
                        "retry_async exhausted %d attempts for %s: %s",
                        max_retries + 1,
                        fn.__name__,
                        exc,
                    )
                    break

                if on_retry:
                    on_retry(attempt + 1, exc)

                logger.warning(
                    "retry_async attempt %d/%d failed for %s: %s (next delay=%.1fs)",
                    attempt + 1,
                    max_retries + 1,
                    fn.__name__,
                    exc,
                    current_delay,
                )

                await asyncio.sleep(current_delay)
                current_delay = min(current_delay * backoff, max_delay)

        raise last_exception  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Miscellaneous
    # ------------------------------------------------------------------

    @staticmethod
    def elapsed_ms(start: float) -> float:
        """Calculate elapsed milliseconds from a perf_counter start.

        Args:
            start: Value from time.perf_counter().

        Returns:
            Elapsed milliseconds.
        """
        return (time.perf_counter() - start) * 1000

    @staticmethod
    def chunk_list(items: list[Any], chunk_size: int) -> list[list[Any]]:
        """Split a list into chunks of a given size.

        Args:
            items: List to split.
            chunk_size: Maximum items per chunk.

        Returns:
            List of sublists.
        """
        if chunk_size <= 0:
            return [items] if items else []
        return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]

    @staticmethod
    def clamp(value: float, min_value: float, max_value: float) -> float:
        """Clamp a numeric value to a range.

        Args:
            value: Value to clamp.
            min_value: Lower bound.
            max_value: Upper bound.

        Returns:
            Clamped value.
        """
        return max(min_value, min(value, max_value))

    @staticmethod
    def truncate(text: str, max_length: int = 100, *, suffix: str = "...") -> str:
        """Truncate text with a suffix if it exceeds max_length.

        Args:
            text: Input text.
            max_length: Maximum total length including suffix.
            suffix: Appended when truncated.

        Returns:
            Original or truncated text.
        """
        if len(text) <= max_length:
            return text
        return text[: max_length - len(suffix)] + suffix

    @staticmethod
    def is_uuid(value: str) -> bool:
        """Check if a string is a valid UUID without raising.

        Args:
            value: String to check.

        Returns:
            True if valid UUID format.
        """
        try:
            UUID(value)
            return True
        except (ValueError, AttributeError):
            return False
