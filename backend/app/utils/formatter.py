"""Response formatting utilities for NeedNow AI.

Standardizes API responses and agent outputs into consistent structures.
Designed for use across FastAPI route handlers, service layers, and
agent pipelines. All formatters produce Pydantic-compatible dicts.

Responsibilities:
    - Format API success/error responses.
    - Format recommendation results.
    - Format memory state responses.
    - Format agent reasoning and output.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ResponseFormatter
# ---------------------------------------------------------------------------


class ResponseFormatter:
    """Standardizes API and agent response formatting.

    Provides static methods that produce consistent JSON-serializable
    dictionaries compatible with Pydantic models and FastAPI responses.
    """

    # ------------------------------------------------------------------
    # API Response Formatters
    # ------------------------------------------------------------------

    @staticmethod
    def success_response(
        data: Any = None,
        *,
        message: str = "Success",
        status_code: int = 200,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Format a standardized success response.

        Args:
            data: Response payload (any JSON-serializable value).
            message: Human-readable success message.
            status_code: HTTP status code for reference.
            meta: Optional metadata (pagination, timing, request_id, etc.).

        Returns:
            Standardized success response dict.
        """
        response: dict[str, Any] = {
            "success": True,
            "status_code": status_code,
            "message": message,
            "data": _serialize(data),
            "timestamp": _utc_now_iso(),
        }

        if meta:
            response["meta"] = meta

        logger.debug("Formatted success response: %s", message)
        return response

    @staticmethod
    def error_response(
        message: str,
        *,
        error_code: str | None = None,
        status_code: int = 400,
        details: Any = None,
        field_errors: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Format a standardized error response.

        Args:
            message: Human-readable error message.
            error_code: Machine-readable error code (e.g., "VALIDATION_ERROR").
            status_code: HTTP status code.
            details: Additional context or debug information.
            field_errors: Per-field validation errors [{field, message}].

        Returns:
            Standardized error response dict.
        """
        response: dict[str, Any] = {
            "success": False,
            "status_code": status_code,
            "message": message,
            "timestamp": _utc_now_iso(),
        }

        if error_code:
            response["error_code"] = error_code
        if details:
            response["details"] = details
        if field_errors:
            response["field_errors"] = field_errors

        logger.debug(
            "Formatted error response: code=%s, message=%s",
            error_code or "UNKNOWN",
            message,
        )
        return response

    # ------------------------------------------------------------------
    # Recommendation Formatters
    # ------------------------------------------------------------------

    @staticmethod
    def format_recommendation(
        user_id: UUID | str,
        products: list[dict[str, Any]],
        *,
        bundles: list[dict[str, Any]] | None = None,
        eco_alternatives: list[dict[str, Any]] | None = None,
        confidence: float = 0.0,
        personalization_applied: bool = False,
        sustainability_score: float = 0.0,
        carbon_saved: float = 0.0,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Format a recommendation response payload.

        Standardizes recommendation output from the RecommendationService
        and agent pipeline into a consistent API response shape.

        Args:
            user_id: Target user identifier.
            products: List of recommended product dicts.
            bundles: Optional bundled product recommendations.
            eco_alternatives: Optional eco-friendly alternatives.
            confidence: Model confidence score (0.0–1.0).
            personalization_applied: Whether user memory was used.
            sustainability_score: Overall sustainability rating (0–100).
            carbon_saved: Total estimated carbon savings (kg).
            context: Optional additional context (urgency, category, etc.).

        Returns:
            Formatted recommendation response dict.
        """
        response: dict[str, Any] = {
            "user_id": str(user_id),
            "recommended_products": products,
            "bundle_products": bundles or [],
            "eco_alternatives": eco_alternatives or [],
            "confidence": round(confidence, 3),
            "personalization_applied": personalization_applied,
            "sustainability": {
                "overall_score": round(sustainability_score, 1),
                "carbon_saved_kg": round(carbon_saved, 2),
            },
            "total_results": len(products),
            "timestamp": _utc_now_iso(),
        }

        if context:
            response["context"] = context

        logger.debug(
            "Formatted recommendation: user=%s, products=%d, confidence=%.3f",
            user_id,
            len(products),
            confidence,
        )
        return response

    # ------------------------------------------------------------------
    # Memory Formatters
    # ------------------------------------------------------------------

    @staticmethod
    def format_memory(
        user_id: UUID | str,
        memory_data: dict[str, Any],
        *,
        memory_type: str | None = None,
        include_metadata: bool = True,
    ) -> dict[str, Any]:
        """Format a memory state response payload.

        Standardizes memory data from the MemoryManager or MemoryRepository
        into a consistent API response shape.

        Args:
            user_id: User identifier.
            memory_data: Raw memory state dict.
            memory_type: Type label (short_term, long_term, preferences).
            include_metadata: Whether to add timestamp and type metadata.

        Returns:
            Formatted memory response dict.
        """
        response: dict[str, Any] = {
            "user_id": str(user_id),
            "memory": _serialize(memory_data),
        }

        if memory_type:
            response["memory_type"] = memory_type

        if include_metadata:
            response["metadata"] = {
                "keys": list(memory_data.keys()) if isinstance(memory_data, dict) else [],
                "timestamp": _utc_now_iso(),
            }

        # Extract summary stats for convenience
        if isinstance(memory_data, dict):
            summary: dict[str, Any] = {}

            if "dietary_preferences" in memory_data:
                summary["dietary_count"] = len(memory_data["dietary_preferences"])
            if "preferred_brands" in memory_data:
                summary["brand_count"] = len(memory_data["preferred_brands"])
            if "sustainability_score" in memory_data:
                summary["sustainability_score"] = memory_data["sustainability_score"]
            if "total_purchases" in memory_data:
                summary["total_purchases"] = memory_data["total_purchases"]

            if summary:
                response["summary"] = summary

        logger.debug(
            "Formatted memory response: user=%s, type=%s, keys=%d",
            user_id,
            memory_type or "all",
            len(memory_data) if isinstance(memory_data, dict) else 0,
        )
        return response

    # ------------------------------------------------------------------
    # Agent Output Formatters
    # ------------------------------------------------------------------

    @staticmethod
    def format_agent_output(
        agent_name: str,
        result: Any,
        *,
        reasoning: str | None = None,
        confidence: float = 0.0,
        execution_time_ms: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Format agent reasoning and output for API responses or logging.

        Standardizes output from supervisor, intent, urgency, product,
        and sustainability agents into a consistent structure.

        Args:
            agent_name: Identifier of the agent (e.g., "supervisor", "urgency").
            result: Agent output payload (will be serialized).
            reasoning: Agent's reasoning chain or explanation text.
            confidence: Agent confidence score (0.0–1.0).
            execution_time_ms: Agent execution duration in milliseconds.
            metadata: Additional agent metadata (model, tokens used, etc.).

        Returns:
            Formatted agent output dict.
        """
        response: dict[str, Any] = {
            "agent": agent_name,
            "result": _serialize(result),
            "confidence": round(confidence, 3),
            "timestamp": _utc_now_iso(),
        }

        if reasoning:
            response["reasoning"] = reasoning

        if execution_time_ms is not None:
            response["execution_time_ms"] = round(execution_time_ms, 1)

        if metadata:
            response["metadata"] = metadata

        logger.debug(
            "Formatted agent output: agent=%s, confidence=%.3f, time=%.1fms",
            agent_name,
            confidence,
            execution_time_ms or 0.0,
        )
        return response

    # ------------------------------------------------------------------
    # Pagination Helper
    # ------------------------------------------------------------------

    @staticmethod
    def paginated_response(
        data: list[Any],
        *,
        total: int,
        page: int = 1,
        page_size: int = 20,
        message: str = "Success",
    ) -> dict[str, Any]:
        """Format a paginated list response.

        Args:
            data: Page of results.
            total: Total number of items across all pages.
            page: Current page number (1-indexed).
            page_size: Items per page.
            message: Human-readable message.

        Returns:
            Standardized paginated response dict.
        """
        total_pages = max(1, (total + page_size - 1) // page_size)

        return {
            "success": True,
            "status_code": 200,
            "message": message,
            "data": [_serialize(item) for item in data],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            },
            "timestamp": _utc_now_iso(),
        }

    # ------------------------------------------------------------------
    # Formatting Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def format_price(amount: float, *, currency: str = "INR") -> str:
        """Format a numeric amount as a price string.

        Args:
            amount: Numeric price.
            currency: Currency code.

        Returns:
            Formatted price string (e.g., "₹1,299.00").
        """
        symbols: dict[str, str] = {
            "INR": "₹",
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
        }
        symbol = symbols.get(currency, f"{currency} ")
        return f"{symbol}{amount:,.2f}"

    @staticmethod
    def format_score(score: float, *, max_score: float = 100.0) -> str:
        """Format a numeric score as a human-readable label.

        Args:
            score: Raw score value.
            max_score: Maximum possible score.

        Returns:
            Label string (e.g., "85.5/100 (Excellent)").
        """
        normalized = (score / max_score) * 100 if max_score > 0 else 0

        if normalized >= 80:
            label = "Excellent"
        elif normalized >= 60:
            label = "Good"
        elif normalized >= 40:
            label = "Fair"
        elif normalized >= 20:
            label = "Low"
        else:
            label = "Poor"

        return f"{score:.1f}/{max_score:.0f} ({label})"

    @staticmethod
    def format_duration(ms: float) -> str:
        """Format a duration in milliseconds as a human-readable string.

        Args:
            ms: Duration in milliseconds.

        Returns:
            Formatted string (e.g., "1.2s", "450ms").
        """
        if ms >= 1000:
            return f"{ms / 1000:.1f}s"
        return f"{ms:.0f}ms"


# ---------------------------------------------------------------------------
# Module-Level Helpers
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _serialize(value: Any) -> Any:
    """Recursively serialize a value for JSON compatibility.

    Handles UUID, datetime, Pydantic models, and nested structures.
    """
    if value is None:
        return None

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, datetime):
        return value.isoformat()

    if hasattr(value, "model_dump"):
        # Pydantic v2
        return value.model_dump()

    if hasattr(value, "dict"):
        # Pydantic v1 fallback
        return value.dict()

    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]

    return value
