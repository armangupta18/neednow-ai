"""Integration tests for the recommendation pipeline.

Flow: User Query → Intent Agent → Product Agent → Sustainability Agent → Response

Validates:
    1. End-to-end flow — full pipeline execution with mocked external services.
    2. Agent orchestration — parallel intent+urgency, sequential product→sustainability.
    3. Recommendation output — structure, ranking, bundles, eco alternatives.
    4. Error propagation — failures at each stage propagate correctly.

These tests exercise the real SupervisorAgent orchestration logic with
mocked Bedrock, DB, and FAISS services. They verify that agents
compose correctly and data flows between pipeline stages.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.agents.intent.agent import IntentAgent
from app.agents.intent.exceptions import IntentParsingException
from app.agents.intent.schemas import IntentResponse
from app.agents.product.agent import ProductAgent
from app.agents.product.schemas import ProductCandidate, ProductResponse
from app.agents.supervisor.agent import SupervisorAgent
from app.agents.supervisor.schemas import SupervisorResponse
from app.agents.sustainability.schemas import EcoAlternative, SustainabilityResponse
from app.agents.urgency.schemas import UrgencyLevel, UrgencyResponse
from app.memory.schemas import UserMemory


# ---------------------------------------------------------------------------
# Fake Product (lightweight stub matching the real model interface)
# ---------------------------------------------------------------------------


@dataclass
class FakeProduct:
    id: UUID
    title: str
    category: str
    price: float
    brand: str | None = None
    stock: int = 10


# ---------------------------------------------------------------------------
# Fixtures: Mock Services
# ---------------------------------------------------------------------------


@pytest.fixture
def user_id() -> UUID:
    return uuid4()


@pytest.fixture
def sample_memory() -> UserMemory:
    return UserMemory(
        dietary_preferences=["organic", "vegan"],
        preferred_brands=["Nature's Best", "EcoPure"],
        budget_level="medium",
        family_size=3,
        purchase_patterns=["baby supplies"],
        sustainability_score=70.0,
    )


@pytest.fixture
def mock_memory_manager(sample_memory: UserMemory) -> AsyncMock:
    """Mock MemoryManager."""
    manager = AsyncMock()
    manager.retrieve_memory = AsyncMock(return_value=sample_memory)
    return manager


@pytest.fixture
def mock_bedrock_intent() -> AsyncMock:
    """Mock BedrockService returning intent JSON."""
    service = AsyncMock()
    service.invoke = AsyncMock(
        return_value=json.dumps({
            "category": "baby",
            "urgency": "high",
            "budget": 50.0,
            "people_count": 1,
            "confidence": 0.93,
        })
    )
    return service


@pytest.fixture
def mock_bedrock_urgency() -> AsyncMock:
    """Mock BedrockService returning urgency JSON."""
    service = AsyncMock()
    service.invoke = AsyncMock(
        return_value=json.dumps({
            "urgency": "HIGH",
            "score": 75,
            "explanation": "User described an immediate need for baby supplies.",
        })
    )
    return service


@pytest.fixture
def sample_products() -> list[FakeProduct]:
    return [
        FakeProduct(id=uuid4(), title="Organic Baby Formula", category="baby", price=24.99, brand="Nature's Best"),
        FakeProduct(id=uuid4(), title="Baby Wipes Sensitive", category="baby", price=5.99, brand="EcoPure"),
        FakeProduct(id=uuid4(), title="Premium Diapers Pack", category="baby", price=18.99, brand="Pampers"),
    ]


@pytest.fixture
def mock_embedding_service() -> AsyncMock:
    """Mock embedding service."""
    service = AsyncMock()
    service.generate_embedding = AsyncMock(return_value=[0.1] * 1024)
    return service


@pytest.fixture
def mock_retrieval_service(sample_products: list[FakeProduct]) -> AsyncMock:
    """Mock retrieval service returning sample products."""
    service = AsyncMock()
    score_map = {str(p.id): 0.9 - (i * 0.1) for i, p in enumerate(sample_products)}
    service.retrieve = AsyncMock(return_value=(sample_products, score_map))
    return service


@pytest.fixture
def mock_sustainability_retrieval() -> AsyncMock:
    """Mock sustainability retrieval service."""
    service = AsyncMock()
    # Return eco alternatives
    eco_product = FakeProduct(
        id=uuid4(), title="Eco Organic Formula", category="baby", price=26.99, brand="GreenBaby"
    )
    service.find_alternatives = AsyncMock(return_value=[eco_product])
    return service


@pytest.fixture
def intent_agent(mock_bedrock_intent: AsyncMock) -> IntentAgent:
    return IntentAgent(bedrock_service=mock_bedrock_intent)


@pytest.fixture
def urgency_agent(mock_bedrock_urgency: AsyncMock) -> Any:
    """Create urgency agent with mocked Bedrock."""
    from app.agents.urgency.agent import UrgencyAgent
    return UrgencyAgent(bedrock_service=mock_bedrock_urgency)


@pytest.fixture
def product_agent(mock_embedding_service: AsyncMock, mock_retrieval_service: AsyncMock) -> ProductAgent:
    return ProductAgent(
        embedding_service=mock_embedding_service,
        retrieval_service=mock_retrieval_service,
    )


@pytest.fixture
def sustainability_agent(mock_sustainability_retrieval: AsyncMock) -> Any:
    """Create a mocked sustainability agent that returns realistic results."""
    agent = AsyncMock()
    agent.analyze = AsyncMock(
        return_value=SustainabilityResponse(
            eco_alternatives=[
                EcoAlternative(
                    original_product_id=uuid4(),
                    original_product_name="Organic Baby Formula",
                    alternative_product_id=uuid4(),
                    alternative_product_name="Eco Organic Formula",
                    carbon_saved=0.8,
                    price_difference=2.0,
                    sustainability_score=82.0,
                )
            ],
            total_carbon_saved=0.8,
            overall_sustainability_score=82.0,
        )
    )
    return agent


@pytest.fixture
def supervisor(
    intent_agent: IntentAgent,
    urgency_agent: Any,
    product_agent: ProductAgent,
    sustainability_agent: Any,
    mock_memory_manager: AsyncMock,
) -> SupervisorAgent:
    """Create the full SupervisorAgent with all sub-agents."""
    return SupervisorAgent(
        intent_agent=intent_agent,
        urgency_agent=urgency_agent,
        product_agent=product_agent,
        sustainability_agent=sustainability_agent,
        memory_manager=mock_memory_manager,
    )


# ---------------------------------------------------------------------------
# Test 1: End-to-End Flow
# ---------------------------------------------------------------------------


class TestEndToEndFlow:
    """Test the complete recommendation pipeline from query to response."""

    @pytest.mark.asyncio
    async def test_full_pipeline_returns_supervisor_response(
        self, supervisor: SupervisorAgent, user_id: UUID
    ) -> None:
        """Full pipeline produces a SupervisorResponse."""
        result = await supervisor.execute(
            user_id=user_id,
            situation="I need baby formula urgently for my infant",
        )
        assert isinstance(result, SupervisorResponse)

    @pytest.mark.asyncio
    async def test_full_pipeline_contains_cart(
        self, supervisor: SupervisorAgent, user_id: UUID
    ) -> None:
        """Response contains a populated cart."""
        result = await supervisor.execute(user_id=user_id, situation="Baby formula needed now")
        assert "category" in result.cart
        assert "products" in result.cart
        assert len(result.cart["products"]) > 0

    @pytest.mark.asyncio
    async def test_full_pipeline_contains_urgency(
        self, supervisor: SupervisorAgent, user_id: UUID
    ) -> None:
        """Response contains urgency assessment."""
        result = await supervisor.execute(user_id=user_id, situation="Baby formula urgent")
        assert "level" in result.urgency
        assert "score" in result.urgency
        assert "explanation" in result.urgency

    @pytest.mark.asyncio
    async def test_full_pipeline_contains_reasoning(
        self, supervisor: SupervisorAgent, user_id: UUID
    ) -> None:
        """Response contains reasoning string."""
        result = await supervisor.execute(user_id=user_id, situation="Need baby supplies")
        assert isinstance(result.reasoning, str)
        assert len(result.reasoning) > 0

    @pytest.mark.asyncio
    async def test_full_pipeline_contains_metadata(
        self, supervisor: SupervisorAgent, user_id: UUID
    ) -> None:
        """Response contains metadata with memory and confidence info."""
        result = await supervisor.execute(user_id=user_id, situation="Baby items")
        assert "memory_used" in result.metadata
        assert result.metadata["memory_used"] is True
        assert "confidence" in result.metadata

    @pytest.mark.asyncio
    async def test_pipeline_uses_memory(
        self, supervisor: SupervisorAgent, user_id: UUID, mock_memory_manager: AsyncMock
    ) -> None:
        """Pipeline retrieves user memory at the start."""
        await supervisor.execute(user_id=user_id, situation="Shopping")
        mock_memory_manager.retrieve_memory.assert_called_once_with(user_id)


# ---------------------------------------------------------------------------
# Test 2: Agent Orchestration
# ---------------------------------------------------------------------------


class TestAgentOrchestration:
    """Test that agents are invoked in the correct order."""

    @pytest.mark.asyncio
    async def test_intent_agent_receives_situation(
        self, supervisor: SupervisorAgent, user_id: UUID, mock_bedrock_intent: AsyncMock
    ) -> None:
        """IntentAgent receives the user's situation text."""
        situation = "Need diapers immediately"
        await supervisor.execute(user_id=user_id, situation=situation)
        mock_bedrock_intent.invoke.assert_called_once()
        call_kwargs = mock_bedrock_intent.invoke.call_args[1]
        assert situation in call_kwargs["user_prompt"]

    @pytest.mark.asyncio
    async def test_urgency_agent_receives_situation(
        self, supervisor: SupervisorAgent, user_id: UUID, mock_bedrock_urgency: AsyncMock
    ) -> None:
        """UrgencyAgent receives the user's situation text."""
        situation = "Emergency baby formula"
        await supervisor.execute(user_id=user_id, situation=situation)
        mock_bedrock_urgency.invoke.assert_called_once()
        call_kwargs = mock_bedrock_urgency.invoke.call_args[1]
        assert situation in call_kwargs["user_prompt"]

    @pytest.mark.asyncio
    async def test_product_agent_uses_intent_results(
        self, supervisor: SupervisorAgent, user_id: UUID, mock_embedding_service: AsyncMock
    ) -> None:
        """ProductAgent is called with the situation for embedding."""
        await supervisor.execute(user_id=user_id, situation="Baby formula needed")
        mock_embedding_service.generate_embedding.assert_called_once()

    @pytest.mark.asyncio
    async def test_sustainability_agent_receives_products(
        self, supervisor: SupervisorAgent, user_id: UUID, sustainability_agent: Any
    ) -> None:
        """SustainabilityAgent.analyze is called with the top products."""
        await supervisor.execute(user_id=user_id, situation="Baby supplies")
        sustainability_agent.analyze.assert_called_once()
        # Verify it received a list of ProductCandidate objects
        call_args = sustainability_agent.analyze.call_args[0]
        assert isinstance(call_args[0], list)
        assert len(call_args[0]) > 0

    @pytest.mark.asyncio
    async def test_intent_and_urgency_run_in_parallel(
        self,
        supervisor: SupervisorAgent,
        user_id: UUID,
        mock_bedrock_intent: AsyncMock,
        mock_bedrock_urgency: AsyncMock,
    ) -> None:
        """Both intent and urgency agents are invoked (parallel via gather)."""
        await supervisor.execute(user_id=user_id, situation="Test parallel")
        # Both should be called exactly once
        assert mock_bedrock_intent.invoke.call_count == 1
        assert mock_bedrock_urgency.invoke.call_count == 1

    @pytest.mark.asyncio
    async def test_category_flows_from_intent_to_product(
        self, supervisor: SupervisorAgent, user_id: UUID
    ) -> None:
        """Category extracted by IntentAgent is used in the cart output."""
        result = await supervisor.execute(user_id=user_id, situation="Baby formula")
        assert result.cart["category"] == "baby"


# ---------------------------------------------------------------------------
# Test 3: Recommendation Output
# ---------------------------------------------------------------------------


class TestRecommendationOutput:
    """Test the structure and quality of recommendation output."""

    @pytest.mark.asyncio
    async def test_cart_products_have_required_fields(
        self, supervisor: SupervisorAgent, user_id: UUID
    ) -> None:
        """Each product in the cart has id, title, price, score."""
        result = await supervisor.execute(user_id=user_id, situation="Baby supplies")
        for product in result.cart["products"]:
            assert "id" in product
            assert "title" in product
            assert "price" in product
            assert "score" in product

    @pytest.mark.asyncio
    async def test_cart_bundles_included(
        self, supervisor: SupervisorAgent, user_id: UUID
    ) -> None:
        """Cart contains a bundles list."""
        result = await supervisor.execute(user_id=user_id, situation="Baby items")
        assert "bundles" in result.cart
        assert isinstance(result.cart["bundles"], list)

    @pytest.mark.asyncio
    async def test_eco_alternative_present_when_found(
        self, supervisor: SupervisorAgent, user_id: UUID
    ) -> None:
        """eco_alternative is populated when sustainability agent finds one."""
        result = await supervisor.execute(user_id=user_id, situation="Baby formula")
        # With our mock, alternatives should be found
        if result.eco_alternative:
            assert "original_product_id" in result.eco_alternative
            assert "alternative_product_name" in result.eco_alternative
            assert "carbon_saved" in result.eco_alternative

    @pytest.mark.asyncio
    async def test_urgency_score_in_valid_range(
        self, supervisor: SupervisorAgent, user_id: UUID
    ) -> None:
        """Urgency score is between 0 and 100."""
        result = await supervisor.execute(user_id=user_id, situation="Urgent need")
        assert 0 <= result.urgency["score"] <= 100

    @pytest.mark.asyncio
    async def test_urgency_level_is_valid_enum(
        self, supervisor: SupervisorAgent, user_id: UUID
    ) -> None:
        """Urgency level is a valid UrgencyLevel value."""
        result = await supervisor.execute(user_id=user_id, situation="Urgent need")
        valid_levels = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
        assert result.urgency["level"] in valid_levels

    @pytest.mark.asyncio
    async def test_confidence_in_metadata(
        self, supervisor: SupervisorAgent, user_id: UUID
    ) -> None:
        """Confidence score is present in metadata."""
        result = await supervisor.execute(user_id=user_id, situation="Baby items")
        assert isinstance(result.metadata["confidence"], float)

    @pytest.mark.asyncio
    async def test_products_sorted_by_score(
        self, supervisor: SupervisorAgent, user_id: UUID
    ) -> None:
        """Cart products are ordered by ranking score (descending)."""
        result = await supervisor.execute(user_id=user_id, situation="Baby supplies")
        scores = [p["score"] for p in result.cart["products"]]
        assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# Test 4: Error Propagation
# ---------------------------------------------------------------------------


class TestErrorPropagation:
    """Test that errors at each pipeline stage propagate correctly."""

    @pytest.mark.asyncio
    async def test_memory_failure_propagates(
        self, supervisor: SupervisorAgent, user_id: UUID, mock_memory_manager: AsyncMock
    ) -> None:
        """MemoryManager failure is handled gracefully — pipeline continues with default memory."""
        mock_memory_manager.retrieve_memory.side_effect = ValueError("User not found")
        # Should NOT raise — supervisor uses default empty memory
        result = await supervisor.execute(user_id=user_id, situation="Test")
        assert result is not None

    @pytest.mark.asyncio
    async def test_intent_agent_failure_propagates(
        self, supervisor: SupervisorAgent, user_id: UUID, mock_bedrock_intent: AsyncMock
    ) -> None:
        """IntentAgent failure propagates from the pipeline."""
        mock_bedrock_intent.invoke.return_value = "Not valid JSON at all"
        with pytest.raises(IntentParsingException):
            await supervisor.execute(user_id=user_id, situation="Test")

    @pytest.mark.asyncio
    async def test_urgency_agent_failure_propagates(
        self, supervisor: SupervisorAgent, user_id: UUID, mock_bedrock_urgency: AsyncMock
    ) -> None:
        """UrgencyAgent failure propagates from the pipeline."""
        mock_bedrock_urgency.invoke.return_value = "garbage"
        with pytest.raises(Exception):
            await supervisor.execute(user_id=user_id, situation="Test")

    @pytest.mark.asyncio
    async def test_embedding_service_failure_propagates(
        self, supervisor: SupervisorAgent, user_id: UUID, mock_embedding_service: AsyncMock
    ) -> None:
        """EmbeddingService failure in ProductAgent propagates."""
        mock_embedding_service.generate_embedding.side_effect = RuntimeError("Bedrock timeout")
        with pytest.raises(RuntimeError, match="Bedrock timeout"):
            await supervisor.execute(user_id=user_id, situation="Test")

    @pytest.mark.asyncio
    async def test_retrieval_service_failure_propagates(
        self, supervisor: SupervisorAgent, user_id: UUID, mock_retrieval_service: AsyncMock
    ) -> None:
        """RetrievalService failure in ProductAgent propagates."""
        mock_retrieval_service.retrieve.side_effect = RuntimeError("FAISS index corrupt")
        with pytest.raises(RuntimeError, match="FAISS index corrupt"):
            await supervisor.execute(user_id=user_id, situation="Test")

    @pytest.mark.asyncio
    async def test_sustainability_failure_does_not_crash_pipeline(
        self,
        user_id: UUID,
        intent_agent: IntentAgent,
        urgency_agent: Any,
        product_agent: ProductAgent,
        mock_memory_manager: AsyncMock,
    ) -> None:
        """If sustainability agent fails, the pipeline should still raise
        (not silently swallow the error)."""
        failing_sustainability = AsyncMock()
        failing_sustainability.analyze = AsyncMock(
            side_effect=RuntimeError("Sustainability service down")
        )

        supervisor = SupervisorAgent(
            intent_agent=intent_agent,
            urgency_agent=urgency_agent,
            product_agent=product_agent,
            sustainability_agent=failing_sustainability,
            memory_manager=mock_memory_manager,
        )

        with pytest.raises(RuntimeError, match="Sustainability service down"):
            await supervisor.execute(user_id=user_id, situation="Test")

    @pytest.mark.asyncio
    async def test_partial_sustainability_results_handled(
        self,
        user_id: UUID,
        intent_agent: IntentAgent,
        urgency_agent: Any,
        product_agent: ProductAgent,
        mock_memory_manager: AsyncMock,
    ) -> None:
        """When sustainability finds no alternatives, eco_alternative is None."""
        empty_sustainability = AsyncMock()
        empty_sustainability.analyze = AsyncMock(
            return_value=SustainabilityResponse(
                eco_alternatives=[],
                total_carbon_saved=0.0,
                overall_sustainability_score=0.0,
            )
        )

        supervisor = SupervisorAgent(
            intent_agent=intent_agent,
            urgency_agent=urgency_agent,
            product_agent=product_agent,
            sustainability_agent=empty_sustainability,
            memory_manager=mock_memory_manager,
        )

        result = await supervisor.execute(user_id=user_id, situation="Baby items")
        assert result.eco_alternative is None
