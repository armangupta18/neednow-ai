"""Request validation utilities for NeedNow AI.

Provides reusable validation logic for user IDs, product IDs, session IDs,
memory payloads, and recommendation requests. Designed for use across
FastAPI route handlers and service layers.

Responsibilities:
    - Validate user input (UUIDs, strings, numerics).
    - Validate product identifiers.
    - Validate session identifiers.
    - Validate memory payloads (structure and content).
    - Validate recommendation requests (completeness and constraints).
"""

from __future__ import annotations

import logging
import re
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ValidationError(Exception):
    """Raised when a validation check fails.

    Attributes:
        field: Name of the field that failed validation.
        message: Human-readable error description.
        value: The invalid value (optional, omitted for sensitive data).
    """

    def __init__(
        self,
        field: str,
        message: str,
        *,
        value: Any = None,
    ) -> None:
        self.field = field
        self.message = message
        self.value = value
        super().__init__(f"{field}: {message}")

    def to_dict(self) -> dict[str, str]:
        """Serialize for API error responses."""
        return {"field": self.field, "message": self.message}


class MultiValidationError(Exception):
    """Raised when multiple validation errors are collected.

    Attributes:
        errors: List of individual ValidationError instances.
    """

    def __init__(self, errors: list[ValidationError]) -> None:
        self.errors = errors
        messages = "; ".join(str(e) for e in errors)
        super().__init__(f"Validation failed: {messages}")

    def to_dict(self) -> list[dict[str, str]]:
        """Serialize all errors for API responses."""
        return [e.to_dict() for e in self.errors]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_URGENCY_LEVELS = {"low", "normal", "medium", "high", "critical", "emergency"}
VALID_BUDGET_LEVELS = {"low", "medium", "high", "premium", "any"}
VALID_MEMORY_TYPES = {"preference", "purchase", "behavior", "short_term", "long_term"}
MAX_CATEGORY_LENGTH = 255
MAX_SITUATION_LENGTH = 2000
MAX_MEMORY_KEYS = 50
MAX_LIST_ITEMS = 100


# ---------------------------------------------------------------------------
# RequestValidator
# ---------------------------------------------------------------------------


class RequestValidator:
    """Validates incoming API request data.

    Provides static methods for domain-specific validation patterns
    used across FastAPI endpoints and service layers. All methods
    raise ValidationError on failure or return the validated/normalized value.
    """

    # Patterns
    _UUID_PATTERN = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )
    _EMAIL_PATTERN = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )

    # ------------------------------------------------------------------
    # UUID Validators
    # ------------------------------------------------------------------

    @staticmethod
    def validate_user_id(value: Any) -> UUID:
        """Validate a user ID (UUID format).

        Args:
            value: Raw user ID value (str or UUID).

        Returns:
            Validated UUID instance.

        Raises:
            ValidationError: If the value is not a valid UUID.
        """
        return RequestValidator._validate_uuid(value, "user_id")

    @staticmethod
    def validate_product_id(value: Any) -> UUID:
        """Validate a product ID (UUID format).

        Args:
            value: Raw product ID value (str or UUID).

        Returns:
            Validated UUID instance.

        Raises:
            ValidationError: If the value is not a valid UUID.
        """
        return RequestValidator._validate_uuid(value, "product_id")

    @staticmethod
    def validate_session_id(value: Any) -> UUID:
        """Validate a session ID (UUID format).

        Args:
            value: Raw session ID value (str or UUID).

        Returns:
            Validated UUID instance.

        Raises:
            ValidationError: If the value is not a valid UUID.
        """
        return RequestValidator._validate_uuid(value, "session_id")

    # ------------------------------------------------------------------
    # Memory Validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_memory_data(data: Any) -> dict[str, Any]:
        """Validate a memory payload structure and content.

        Checks that the payload is a dict, doesn't exceed key limits,
        and contains valid memory field types.

        Args:
            data: Raw memory payload.

        Returns:
            Validated memory data dict.

        Raises:
            ValidationError: If the payload structure is invalid.
            MultiValidationError: If multiple fields fail validation.
        """
        if data is None:
            raise ValidationError("memory_data", "Memory data must not be null")

        if not isinstance(data, dict):
            raise ValidationError(
                "memory_data",
                f"Expected a JSON object, got {type(data).__name__}",
            )

        if len(data) > MAX_MEMORY_KEYS:
            raise ValidationError(
                "memory_data",
                f"Memory payload exceeds maximum keys ({MAX_MEMORY_KEYS})",
            )

        errors: list[ValidationError] = []

        # Validate known fields if present
        if "dietary_preferences" in data:
            if not isinstance(data["dietary_preferences"], list):
                errors.append(
                    ValidationError("dietary_preferences", "Must be a list of strings")
                )
            elif len(data["dietary_preferences"]) > MAX_LIST_ITEMS:
                errors.append(
                    ValidationError(
                        "dietary_preferences",
                        f"Exceeds maximum items ({MAX_LIST_ITEMS})",
                    )
                )

        if "preferred_brands" in data:
            if not isinstance(data["preferred_brands"], list):
                errors.append(
                    ValidationError("preferred_brands", "Must be a list of strings")
                )
            elif len(data["preferred_brands"]) > MAX_LIST_ITEMS:
                errors.append(
                    ValidationError(
                        "preferred_brands",
                        f"Exceeds maximum items ({MAX_LIST_ITEMS})",
                    )
                )

        if "budget_level" in data:
            budget = data["budget_level"]
            if budget is not None and str(budget).lower() not in VALID_BUDGET_LEVELS:
                errors.append(
                    ValidationError(
                        "budget_level",
                        f"Must be one of: {', '.join(sorted(VALID_BUDGET_LEVELS))}",
                    )
                )

        if "family_size" in data:
            fs = data["family_size"]
            if fs is not None:
                if not isinstance(fs, int) or fs < 1 or fs > 50:
                    errors.append(
                        ValidationError("family_size", "Must be an integer between 1 and 50")
                    )

        if "sustainability_score" in data:
            score = data["sustainability_score"]
            if not isinstance(score, (int, float)) or score < 0 or score > 100:
                errors.append(
                    ValidationError(
                        "sustainability_score", "Must be a number between 0 and 100"
                    )
                )

        if "memory_type" in data:
            mtype = data["memory_type"]
            if mtype not in VALID_MEMORY_TYPES:
                errors.append(
                    ValidationError(
                        "memory_type",
                        f"Must be one of: {', '.join(sorted(VALID_MEMORY_TYPES))}",
                    )
                )

        if errors:
            logger.warning(
                "Memory data validation failed: %d errors", len(errors)
            )
            raise MultiValidationError(errors)

        logger.debug("Memory data validated successfully (%d keys)", len(data))
        return data

    # ------------------------------------------------------------------
    # Request Validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_request(data: dict[str, Any]) -> dict[str, Any]:
        """Validate a recommendation or general API request payload.

        Checks for required fields, validates UUIDs, urgency levels,
        categories, and budget constraints.

        Args:
            data: Request payload dict.

        Returns:
            Validated and normalized request dict.

        Raises:
            ValidationError: If a required field is missing or invalid.
            MultiValidationError: If multiple fields fail validation.
        """
        if not isinstance(data, dict):
            raise ValidationError("request", "Request body must be a JSON object")

        errors: list[ValidationError] = []

        # Validate user_id (required)
        if "user_id" in data:
            try:
                data["user_id"] = RequestValidator.validate_user_id(data["user_id"])
            except ValidationError as e:
                errors.append(e)
        else:
            errors.append(ValidationError("user_id", "Required field is missing"))

        # Validate situation (required for recommendations)
        if "situation" in data:
            situation = data["situation"]
            if not isinstance(situation, str) or not situation.strip():
                errors.append(ValidationError("situation", "Must be a non-empty string"))
            elif len(situation) > MAX_SITUATION_LENGTH:
                errors.append(
                    ValidationError(
                        "situation",
                        f"Must be {MAX_SITUATION_LENGTH} characters or fewer",
                    )
                )
            else:
                data["situation"] = situation.strip()

        # Validate urgency
        if "urgency" in data:
            urgency = str(data["urgency"]).lower().strip()
            if urgency not in VALID_URGENCY_LEVELS:
                errors.append(
                    ValidationError(
                        "urgency",
                        f"Must be one of: {', '.join(sorted(VALID_URGENCY_LEVELS))}",
                    )
                )
            else:
                data["urgency"] = urgency

        # Validate category
        if "category" in data:
            category = data["category"]
            if not isinstance(category, str) or not category.strip():
                errors.append(ValidationError("category", "Must be a non-empty string"))
            elif len(category) > MAX_CATEGORY_LENGTH:
                errors.append(
                    ValidationError(
                        "category",
                        f"Must be {MAX_CATEGORY_LENGTH} characters or fewer",
                    )
                )
            else:
                data["category"] = category.strip()

        # Validate budget
        if "budget" in data:
            budget = data["budget"]
            if budget is not None:
                try:
                    budget_val = float(budget)
                    if budget_val < 0:
                        errors.append(
                            ValidationError("budget", "Must be a non-negative number")
                        )
                    else:
                        data["budget"] = budget_val
                except (TypeError, ValueError):
                    errors.append(
                        ValidationError("budget", "Must be a valid number")
                    )

        # Validate product_id if present
        if "product_id" in data:
            try:
                data["product_id"] = RequestValidator.validate_product_id(data["product_id"])
            except ValidationError as e:
                errors.append(e)

        # Validate product_ids list if present
        if "product_ids" in data:
            pids = data["product_ids"]
            if not isinstance(pids, list):
                errors.append(ValidationError("product_ids", "Must be a list of UUIDs"))
            elif len(pids) == 0:
                errors.append(ValidationError("product_ids", "Must contain at least one ID"))
            elif len(pids) > MAX_LIST_ITEMS:
                errors.append(
                    ValidationError(
                        "product_ids",
                        f"Exceeds maximum items ({MAX_LIST_ITEMS})",
                    )
                )
            else:
                validated_ids: list[UUID] = []
                for i, pid in enumerate(pids):
                    try:
                        validated_ids.append(
                            RequestValidator._validate_uuid(pid, f"product_ids[{i}]")
                        )
                    except ValidationError as e:
                        errors.append(e)
                data["product_ids"] = validated_ids

        # Validate quantity if present
        if "quantity" in data:
            qty = data["quantity"]
            if not isinstance(qty, int) or qty < 1:
                errors.append(
                    ValidationError("quantity", "Must be a positive integer")
                )

        if errors:
            logger.warning(
                "Request validation failed: %d errors for fields [%s]",
                len(errors),
                ", ".join(e.field for e in errors),
            )
            raise MultiValidationError(errors)

        logger.debug("Request validated successfully")
        return data

    # ------------------------------------------------------------------
    # Generic Validators
    # ------------------------------------------------------------------

    @staticmethod
    def validate_email(email: str) -> str:
        """Validate an email address format.

        Args:
            email: Email string.

        Returns:
            Normalized (lowercased, stripped) email.

        Raises:
            ValidationError: If the format is invalid.
        """
        normalized = email.strip().lower()
        if not RequestValidator._EMAIL_PATTERN.match(normalized):
            raise ValidationError("email", "Invalid email format")
        if len(normalized) > 255:
            raise ValidationError("email", "Email must be 255 characters or fewer")
        return normalized

    @staticmethod
    def validate_non_empty(value: str, field: str) -> str:
        """Validate that a string is non-empty after stripping.

        Args:
            value: String to check.
            field: Field name for error messages.

        Returns:
            Stripped string.

        Raises:
            ValidationError: If the string is empty.
        """
        stripped = value.strip()
        if not stripped:
            raise ValidationError(field, "Must not be empty")
        return stripped

    @staticmethod
    def validate_positive(value: float | int, field: str) -> float:
        """Validate that a number is positive.

        Args:
            value: Number to check.
            field: Field name for error messages.

        Returns:
            The validated number as float.

        Raises:
            ValidationError: If the value is not positive.
        """
        if value <= 0:
            raise ValidationError(field, "Must be a positive number")
        return float(value)

    @staticmethod
    def validate_in_range(
        value: float | int,
        field: str,
        *,
        min_value: float = 0.0,
        max_value: float = float("inf"),
    ) -> float:
        """Validate that a number falls within a range.

        Args:
            value: Number to check.
            field: Field name for error messages.
            min_value: Minimum allowed value (inclusive).
            max_value: Maximum allowed value (inclusive).

        Returns:
            The validated number as float.

        Raises:
            ValidationError: If the value is out of range.
        """
        if value < min_value or value > max_value:
            raise ValidationError(
                field, f"Must be between {min_value} and {max_value}"
            )
        return float(value)

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_uuid(value: Any, field: str) -> UUID:
        """Validate and parse a UUID value.

        Args:
            value: Raw value (str, UUID, or other).
            field: Field name for error messages.

        Returns:
            Validated UUID instance.

        Raises:
            ValidationError: If the value is not a valid UUID.
        """
        if value is None:
            raise ValidationError(field, "Must not be null")

        if isinstance(value, UUID):
            return value

        if not isinstance(value, str):
            raise ValidationError(
                field, f"Expected a UUID string, got {type(value).__name__}"
            )

        value = value.strip()

        if not value:
            raise ValidationError(field, "Must not be empty")

        try:
            return UUID(value)
        except (ValueError, AttributeError) as exc:
            raise ValidationError(
                field, f"Invalid UUID format: '{value}'"
            ) from exc
