"""Tests for the Intent Agent (app/agents/intent).

Covers:
    1. Intent extraction — correct category, urgency, budget, people_count.
    2. Confidence score — valid range, high vs low confidence scenarios.
    3. Invalid input — malformed JSON, missing fields, bad types.
    4. Empty query — handling of empty/blank user input.
    5. Agent response structure — Pydantic model validation.

Tests the IntentAgent (with mocked GeminiService) and IntentParser
directly to verify both the orchestration and parsing layers.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.agents.intent.agent import IntentAgent
from app.agents.intent.exceptions import (
    IntentAgentException,
    IntentParsingException,
    IntentValidationException,
)
from app.agents.intent.parser import IntentParser
from app.agents.intent.schemas import IntentResponse


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_llm() -> AsyncMock:
    """Create a mocked GeminiService."""
    service = AsyncMock()
    return service


@pytest.fixture
def intent_agent(mock_llm: AsyncMock) -> IntentAgent:
    """Create an IntentAgent with mocked LLM."""
    return IntentAgent(llm_service=mock_llm)


def _make_response(
    intent: str = "grocery_restock",
    category: str = "groceries",
    urgency: str = "medium",
    keywords: list[str] | None = None,
    budget: float | None = None,
    people_count: int | None = None,
    confidence: float = 0.9,
) -> str:
    """Helper to build a mock LLM JSON response string."""
    data = {
        "intent": intent,
        "urgency": urgency,
        "category": category,
        "keywords": keywords or ["product"],
        "budget": budget,
        "people_count": people_count,
        "confidence": confidence,
    }
    return json.dumps(data)


# ---------------------------------------------------------------------------
# Test 1: Intent Extraction
# ---------------------------------------------------------------------------


class TestIntentExtraction:
    """Test that the agent correctly extracts intent fields."""

    @pytest.mark.asyncio
    async def test_extracts_grocery_intent(
        self, intent_agent: IntentAgent, mock_llm: AsyncMock
    ) -> None:
        """Extracts a groceries category from user input."""
        mock_llm.invoke.return_value = _make_response(
            category="groceries", urgency="medium", confidence=0.92
        )
        result = await intent_agent.analyze("I need milk and bread for dinner")

        assert result.category == "groceries"
        assert result.urgency == "medium"

    @pytest.mark.asyncio
    async def test_extracts_medical_intent(
        self, intent_agent: IntentAgent, mock_llm: AsyncMock
    ) -> None:
        """Extracts a medical category."""
        mock_llm.invoke.return_value = _make_response(
            category="medical", urgency="critical", confidence=0.97
        )
        result = await intent_agent.analyze("My child has a fever and needs medicine now")

        assert result.category == "medical"
        assert result.urgency == "critical"

    @pytest.mark.asyncio
    async def test_extracts_budget(
        self, intent_agent: IntentAgent, mock_llm: AsyncMock
    ) -> None:
        """Extracts budget when mentioned."""
        mock_llm.invoke.return_value = _make_response(
            category="party", urgency="high", budget=50.0, confidence=0.88
        )
        result = await intent_agent.analyze("Party snacks under $50, guests arriving soon")

        assert result.budget == 50.0

    @pytest.mark.asyncio
    async def test_extracts_people_count(
        self, intent_agent: IntentAgent, mock_llm: AsyncMock
    ) -> None:
        """Extracts people count."""
        mock_llm.invoke.return_value = _make_response(
            category="party", urgency="high", people_count=8, confidence=0.85
        )
        result = await intent_agent.analyze("Hosting 8 people for dinner tonight")

        assert result.people_count == 8

    @pytest.mark.asyncio
    async def test_null_budget_and_people_count(
        self, intent_agent: IntentAgent, mock_llm: AsyncMock
    ) -> None:
        """Budget and people_count are None when not mentioned."""
        mock_llm.invoke.return_value = _make_response(
            category="cleaning", urgency="low"
        )
        result = await intent_agent.analyze("I should buy cleaning supplies sometime")

        assert result.budget is None
        assert result.people_count is None

    @pytest.mark.asyncio
    async def test_passes_user_input_to_llm(
        self, intent_agent: IntentAgent, mock_llm: AsyncMock
    ) -> None:
        """User input is forwarded to Gemini as user_prompt."""
        mock_llm.invoke.return_value = _make_response()
        user_text = "Need diapers for my baby"

        await intent_agent.analyze(user_text)

        mock_llm.invoke.assert_called_once()
        call_kwargs = mock_llm.invoke.call_args[1]
        assert call_kwargs["user_prompt"] == user_text


# ---------------------------------------------------------------------------
# Test 2: Confidence Score
# ---------------------------------------------------------------------------


class TestConfidenceScore:
    """Test confidence score handling."""

    @pytest.mark.asyncio
    async def test_high_confidence_score(
        self, intent_agent: IntentAgent, mock_llm: AsyncMock
    ) -> None:
        """High confidence when input is clear."""
        mock_llm.invoke.return_value = _make_response(confidence=0.97)
        result = await intent_agent.analyze("Buy eggs and milk")
        assert result.confidence == 0.97

    @pytest.mark.asyncio
    async def test_low_confidence_score(
        self, intent_agent: IntentAgent, mock_llm: AsyncMock
    ) -> None:
        """Low confidence when input is ambiguous."""
        mock_llm.invoke.return_value = _make_response(confidence=0.35)
        result = await intent_agent.analyze("hmm maybe something")
        assert result.confidence == 0.35

    @pytest.mark.asyncio
    async def test_confidence_at_boundary_zero(
        self, intent_agent: IntentAgent, mock_llm: AsyncMock
    ) -> None:
        """Confidence of 0.0 is valid."""
        mock_llm.invoke.return_value = _make_response(confidence=0.0)
        result = await intent_agent.analyze("...")
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_confidence_at_boundary_one(
        self, intent_agent: IntentAgent, mock_llm: AsyncMock
    ) -> None:
        """Confidence of 1.0 is valid."""
        mock_llm.invoke.return_value = _make_response(confidence=1.0)
        result = await intent_agent.analyze("I urgently need insulin right now")
        assert result.confidence == 1.0

    def test_parser_rejects_confidence_above_one(self) -> None:
        """Confidence > 1.0 is rejected by schema validation."""
        raw = _make_response(confidence=1.5)
        with pytest.raises(IntentValidationException):
            IntentParser.parse(raw)

    def test_parser_rejects_confidence_below_zero(self) -> None:
        """Confidence < 0.0 is rejected by schema validation."""
        raw = _make_response(confidence=-0.1)
        with pytest.raises(IntentValidationException):
            IntentParser.parse(raw)


# ---------------------------------------------------------------------------
# Test 3: Invalid Input (Parser Errors)
# ---------------------------------------------------------------------------


class TestInvalidInput:
    """Test handling of invalid/malformed LLM responses."""

    def test_parser_rejects_non_json(self) -> None:
        """Non-JSON text raises IntentParsingException."""
        with pytest.raises(IntentParsingException):
            IntentParser.parse("This is not JSON at all")

    def test_parser_rejects_empty_json(self) -> None:
        """Empty JSON object raises IntentValidationException."""
        with pytest.raises(IntentValidationException):
            IntentParser.parse("{}")

    def test_parser_rejects_missing_category(self) -> None:
        """Missing required 'category' raises IntentValidationException."""
        raw = json.dumps({"urgency": "low", "confidence": 0.5})
        with pytest.raises(IntentValidationException):
            IntentParser.parse(raw)

    def test_parser_rejects_missing_urgency(self) -> None:
        """Missing required 'urgency' raises IntentValidationException."""
        raw = json.dumps({"category": "groceries", "confidence": 0.5})
        with pytest.raises(IntentValidationException):
            IntentParser.parse(raw)

    def test_parser_rejects_invalid_urgency_value(self) -> None:
        """Invalid urgency literal raises IntentValidationException."""
        raw = json.dumps({"category": "groceries", "urgency": "extreme", "confidence": 0.5})
        with pytest.raises(IntentValidationException):
            IntentParser.parse(raw)

    def test_parser_rejects_non_numeric_confidence(self) -> None:
        """Non-numeric confidence raises IntentValidationException."""
        raw = json.dumps({"category": "groceries", "urgency": "low", "confidence": "high"})
        with pytest.raises(IntentValidationException):
            IntentParser.parse(raw)

    def test_parser_handles_markdown_wrapped_json(self) -> None:
        """Parser strips ```json markdown fences."""
        raw = '```json\n{"intent": "baby_care", "category": "baby", "urgency": "high", "keywords": ["formula"], "confidence": 0.9}\n```'
        result = IntentParser.parse(raw)
        assert result.intent == "baby_care"
        assert result.category == "baby"
        assert result.urgency == "high"

    def test_parser_rejects_array_response(self) -> None:
        """JSON array instead of object raises an exception."""
        with pytest.raises((IntentParsingException, IntentValidationException, TypeError)):
            IntentParser.parse('[{"category": "food"}]')

    @pytest.mark.asyncio
    async def test_agent_propagates_parsing_exception(
        self, intent_agent: IntentAgent, mock_llm: AsyncMock
    ) -> None:
        """IntentParsingException propagates from agent.analyze."""
        mock_llm.invoke.return_value = "Totally garbled output from LLM"
        with pytest.raises(IntentParsingException):
            await intent_agent.analyze("Some valid user input")

    @pytest.mark.asyncio
    async def test_agent_propagates_validation_exception(
        self, intent_agent: IntentAgent, mock_llm: AsyncMock
    ) -> None:
        """IntentValidationException propagates from agent.analyze."""
        mock_llm.invoke.return_value = json.dumps({"category": "food"})
        with pytest.raises(IntentValidationException):
            await intent_agent.analyze("Some valid user input")


# ---------------------------------------------------------------------------
# Test 4: Empty Query
# ---------------------------------------------------------------------------


class TestEmptyQuery:
    """Test handling of empty or blank user input."""

    @pytest.mark.asyncio
    async def test_empty_string_passed_to_llm(
        self, intent_agent: IntentAgent, mock_llm: AsyncMock
    ) -> None:
        """Empty string is still passed to Gemini (validation is at API layer)."""
        mock_llm.invoke.return_value = _make_response(
            category="other", urgency="low", confidence=0.1
        )
        result = await intent_agent.analyze("")
        assert result.category == "other"
        assert result.confidence == 0.1

    @pytest.mark.asyncio
    async def test_whitespace_only_passed_to_llm(
        self, intent_agent: IntentAgent, mock_llm: AsyncMock
    ) -> None:
        """Whitespace-only input is passed to Gemini."""
        mock_llm.invoke.return_value = _make_response(
            category="other", urgency="low", confidence=0.05
        )
        result = await intent_agent.analyze("   \t\n  ")
        assert result.confidence <= 0.1

    @pytest.mark.asyncio
    async def test_llm_called_even_for_empty_input(
        self, intent_agent: IntentAgent, mock_llm: AsyncMock
    ) -> None:
        """Gemini is still invoked for empty input (agent doesn't pre-filter)."""
        mock_llm.invoke.return_value = _make_response()
        await intent_agent.analyze("")
        mock_llm.invoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_single_word_input(
        self, intent_agent: IntentAgent, mock_llm: AsyncMock
    ) -> None:
        """Single word input is handled."""
        mock_llm.invoke.return_value = _make_response(
            category="other", urgency="low", confidence=0.3
        )
        result = await intent_agent.analyze("help")
        assert result.category == "other"


# ---------------------------------------------------------------------------
# Test 5: Agent Response Structure
# ---------------------------------------------------------------------------


class TestAgentResponseStructure:
    """Test that IntentResponse Pydantic model structure is correct."""

    def test_response_has_required_fields(self) -> None:
        """IntentResponse requires intent, category, urgency, confidence."""
        response = IntentResponse(
            intent="grocery_restock", category="groceries", urgency="medium", confidence=0.8
        )
        assert response.intent == "grocery_restock"
        assert response.category == "groceries"
        assert response.urgency == "medium"
        assert response.confidence == 0.8

    def test_response_optional_fields_default_to_none(self) -> None:
        """budget and people_count default to None."""
        response = IntentResponse(
            intent="food_shopping", category="food", urgency="low", confidence=0.5
        )
        assert response.budget is None
        assert response.people_count is None

    def test_response_with_all_fields(self) -> None:
        """Response with all fields populated."""
        response = IntentResponse(
            intent="party_supplies",
            category="party",
            urgency="high",
            keywords=["chips", "drinks"],
            budget=100.0,
            people_count=12,
            confidence=0.95,
        )
        assert response.budget == 100.0
        assert response.people_count == 12
        assert response.keywords == ["chips", "drinks"]

    def test_response_serialization(self) -> None:
        """Response serializes to dict correctly."""
        response = IntentResponse(
            intent="medical_supplies",
            category="medical",
            urgency="critical",
            keywords=["bandage"],
            budget=None,
            people_count=1,
            confidence=0.99,
        )
        data = response.model_dump()
        assert data["intent"] == "medical_supplies"
        assert data["category"] == "medical"
        assert data["urgency"] == "critical"
        assert data["budget"] is None
        assert data["people_count"] == 1
        assert data["confidence"] == 0.99

    def test_response_json_serialization(self) -> None:
        """Response serializes to JSON string."""
        response = IntentResponse(
            intent="baby_care", category="baby", urgency="high", confidence=0.88
        )
        json_str = response.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["intent"] == "baby_care"
        assert parsed["category"] == "baby"

    def test_response_urgency_literal_values(self) -> None:
        """Only allowed urgency literals are accepted."""
        for urgency in ["low", "medium", "high", "critical"]:
            response = IntentResponse(
                intent="test", category="other", urgency=urgency, confidence=0.5
            )
            assert response.urgency == urgency

    def test_response_rejects_invalid_urgency(self) -> None:
        """Invalid urgency value is rejected."""
        with pytest.raises(Exception):
            IntentResponse(intent="test", category="other", urgency="extreme", confidence=0.5)

    @pytest.mark.asyncio
    async def test_agent_returns_intent_response_type(
        self, intent_agent: IntentAgent, mock_llm: AsyncMock
    ) -> None:
        """Agent.analyze returns an IntentResponse instance."""
        mock_llm.invoke.return_value = _make_response()
        result = await intent_agent.analyze("Buy groceries")
        assert isinstance(result, IntentResponse)

    @pytest.mark.asyncio
    async def test_full_pipeline_response(
        self, intent_agent: IntentAgent, mock_llm: AsyncMock
    ) -> None:
        """End-to-end: input → LLM mock → parsed IntentResponse."""
        mock_llm.invoke.return_value = json.dumps({
            "intent": "baby_care",
            "category": "baby",
            "urgency": "critical",
            "keywords": ["baby formula", "diapers"],
            "budget": 30.0,
            "people_count": 1,
            "confidence": 0.96,
        })
        result = await intent_agent.analyze("My newborn needs formula immediately")

        assert result.intent == "baby_care"
        assert result.category == "baby"
        assert result.urgency == "critical"
        assert result.keywords == ["baby formula", "diapers"]
        assert result.budget == 30.0
        assert result.people_count == 1
        assert result.confidence == 0.96
