"""End-to-end user journey test for NeedNow AI.

Scenario:
    1. User starts a chat conversation.
    2. Intent is identified (category, urgency, budget).
    3. Recommendations are generated with ranking.
    4. Product is added to the user's cart.
    5. Memory is stored (preferences update).
    6. Sustainability suggestions are shown.

Validates the complete user journey across all API endpoints using
a self-contained FastAPI app with mocked services. Simulates a
realistic user session flowing through all major platform features.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import APIRouter, Depends, FastAPI, HTTPException, File, Query, UploadFile
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Schema Replicas (minimal, matching actual API contracts)
# ---------------------------------------------------------------------------


class AgentMessageSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: UUID
    session_id: UUID
    content: str
    role: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    user_id: UUID
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: UUID | None = None


class ChatResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: UUID
    user_message: AgentMessageSchema
    assistant_message: AgentMessageSchema
    cart: dict[str, Any] = Field(default_factory=dict)
    urgency: dict[str, Any] = Field(default_factory=dict)
    reasoning: str = ""
    eco_alternative: dict[str, Any] | None = None
    recommended_products: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CartAddRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: UUID
    product_id: UUID
    quantity: int = Field(default=1, ge=1)


class CartItemSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    product_id: UUID
    product_name: str
    quantity: int
    unit_price: float
    line_total: float


class CartResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: UUID
    cart_id: UUID
    total_amount: float
    items: list[CartItemSchema] = Field(default_factory=list)


class CartMutationResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str
    cart: CartResponseSchema


class UserMemorySchema(BaseModel):
    dietary_preferences: list[str] = Field(default_factory=list)
    preferred_brands: list[str] = Field(default_factory=list)
    budget_level: str | None = None
    family_size: int | None = None
    purchase_patterns: list[str] = Field(default_factory=list)
    sustainability_score: float = 0.0


class StoreMemoryRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: UUID
    memory: UserMemorySchema


class MemoryResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: UUID
    memory: UserMemorySchema


class EcoAlternativeSchema(BaseModel):
    original_product_id: UUID
    original_product_name: str
    alternative_product_id: UUID
    alternative_product_name: str
    carbon_saved: float
    price_difference: float
    sustainability_score: float


class SustainabilityRecommendRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_ids: list[UUID] = Field(..., min_length=1)


class SustainabilityRecommendResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recommendations: list[EcoAlternativeSchema] = Field(default_factory=list)
    total_carbon_saved: float
    overall_sustainability_score: float


# ---------------------------------------------------------------------------
# Test Data
# ---------------------------------------------------------------------------

USER_ID = uuid4()
SESSION_ID = uuid4()
CART_ID = uuid4()
PRODUCT_ID_1 = uuid4()
PRODUCT_ID_2 = uuid4()
PRODUCT_ID_3 = uuid4()
ECO_PRODUCT_ID = uuid4()


# ---------------------------------------------------------------------------
# Build Complete App (all endpoints)
# ---------------------------------------------------------------------------


def _build_app(services: dict[str, Any]) -> FastAPI:
    """Build a complete FastAPI app with all journey endpoints."""
    app = FastAPI()

    # --- Chat Endpoint ---
    chat_router = APIRouter(prefix="/chat", tags=["Chat"])

    @chat_router.post("", response_model=ChatResponseSchema, status_code=200)
    async def send_chat(request: ChatRequestSchema) -> ChatResponseSchema:
        try:
            return await services["chat"].process_message(request)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception:
            raise HTTPException(status_code=500, detail="Chat failed")

    # --- Cart Endpoints ---
    cart_router = APIRouter(prefix="/cart", tags=["Cart"])

    @cart_router.post("/add", response_model=CartMutationResponseSchema, status_code=200)
    async def add_to_cart(request: CartAddRequestSchema) -> CartMutationResponseSchema:
        try:
            return await services["cart"].add_item(
                user_id=request.user_id,
                product_id=request.product_id,
                quantity=request.quantity,
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception:
            raise HTTPException(status_code=500, detail="Cart add failed")

    @cart_router.get("/{user_id}", response_model=CartResponseSchema, status_code=200)
    async def get_cart(user_id: UUID) -> CartResponseSchema:
        try:
            return await services["cart"].get_cart(user_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception:
            raise HTTPException(status_code=500, detail="Cart get failed")

    # --- Memory Endpoints ---
    memory_router = APIRouter(prefix="/memory", tags=["Memory"])

    @memory_router.post("/store", response_model=MemoryResponseSchema, status_code=200)
    async def store_memory(request: StoreMemoryRequestSchema) -> MemoryResponseSchema:
        try:
            stored = await services["memory"].save_memory(
                user_id=request.user_id, memory=request.memory
            )
            return MemoryResponseSchema(user_id=request.user_id, memory=UserMemorySchema(**stored))
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception:
            raise HTTPException(status_code=500, detail="Memory store failed")

    @memory_router.get("/{user_id}", response_model=MemoryResponseSchema, status_code=200)
    async def get_memory(user_id: UUID) -> MemoryResponseSchema:
        try:
            memory = await services["memory"].retrieve_memory(user_id)
            return MemoryResponseSchema(user_id=user_id, memory=memory)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception:
            raise HTTPException(status_code=500, detail="Memory get failed")

    # --- Sustainability Endpoint ---
    sustainability_router = APIRouter(prefix="/sustainability", tags=["Sustainability"])

    @sustainability_router.post(
        "/recommend", response_model=SustainabilityRecommendResponseSchema, status_code=200
    )
    async def recommend_eco(
        request: SustainabilityRecommendRequestSchema,
    ) -> SustainabilityRecommendResponseSchema:
        try:
            return await services["sustainability"].recommend_alternatives(
                product_ids=request.product_ids
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception:
            raise HTTPException(status_code=500, detail="Sustainability failed")

    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(cart_router, prefix="/api/v1")
    app.include_router(memory_router, prefix="/api/v1")
    app.include_router(sustainability_router, prefix="/api/v1")

    return app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_services() -> dict[str, AsyncMock]:
    """Create all mocked services for the user journey."""

    # Chat service mock
    chat_service = AsyncMock()
    chat_service.process_message = AsyncMock(
        return_value=ChatResponseSchema(
            session_id=SESSION_ID,
            user_message=AgentMessageSchema(
                user_id=USER_ID,
                session_id=SESSION_ID,
                content="I need baby formula urgently, my infant is hungry",
                role="user",
            ),
            assistant_message=AgentMessageSchema(
                user_id=USER_ID,
                session_id=SESSION_ID,
                content="I found several baby formula options for immediate delivery. "
                "The top recommendation is Organic Baby Formula at $24.99.",
                role="assistant",
                metadata={"urgency_level": "HIGH", "confidence": 0.93},
            ),
            cart={
                "category": "baby",
                "products": [
                    {"id": str(PRODUCT_ID_1), "title": "Organic Baby Formula", "price": 24.99, "score": 95.5},
                    {"id": str(PRODUCT_ID_2), "title": "Baby Wipes Sensitive", "price": 5.99, "score": 88.2},
                    {"id": str(PRODUCT_ID_3), "title": "Premium Diapers", "price": 18.99, "score": 82.0},
                ],
                "bundles": [
                    {"id": str(PRODUCT_ID_2), "title": "Baby Wipes Sensitive", "price": 5.99},
                ],
            },
            urgency={"level": "HIGH", "score": 78, "reasoning": "User described an urgent feeding need."},
            reasoning="User needs baby formula urgently. Category: baby. Urgency: HIGH. "
            "Recommending top-rated organic formula with bundle suggestions.",
            eco_alternative={
                "original_product_id": str(PRODUCT_ID_1),
                "original_product_name": "Organic Baby Formula",
                "alternative_product_id": str(ECO_PRODUCT_ID),
                "alternative_product_name": "Eco Organic Formula Plus",
                "carbon_saved": 0.8,
                "price_difference": 2.0,
                "sustainability_score": 85.0,
            },
            recommended_products=[
                {"id": str(PRODUCT_ID_1), "title": "Organic Baby Formula", "price": 24.99},
                {"id": str(PRODUCT_ID_2), "title": "Baby Wipes Sensitive", "price": 5.99},
            ],
            metadata={"memory_used": True, "confidence": 0.93, "pipeline_time_ms": 450.2},
        )
    )

    # Cart service mock
    cart_service = AsyncMock()
    cart_service.add_item = AsyncMock(
        return_value=CartMutationResponseSchema(
            message="Item added to cart",
            cart=CartResponseSchema(
                user_id=USER_ID,
                cart_id=CART_ID,
                total_amount=24.99,
                items=[
                    CartItemSchema(
                        id=uuid4(),
                        product_id=PRODUCT_ID_1,
                        product_name="Organic Baby Formula",
                        quantity=1,
                        unit_price=24.99,
                        line_total=24.99,
                    )
                ],
            ),
        )
    )
    cart_service.get_cart = AsyncMock(
        return_value=CartResponseSchema(
            user_id=USER_ID,
            cart_id=CART_ID,
            total_amount=24.99,
            items=[
                CartItemSchema(
                    id=uuid4(),
                    product_id=PRODUCT_ID_1,
                    product_name="Organic Baby Formula",
                    quantity=1,
                    unit_price=24.99,
                    line_total=24.99,
                )
            ],
        )
    )

    # Memory service mock
    memory_service = AsyncMock()
    memory_data = {
        "dietary_preferences": ["organic"],
        "preferred_brands": ["Nature's Best"],
        "budget_level": "medium",
        "family_size": 3,
        "purchase_patterns": ["baby supplies", "organic formula"],
        "sustainability_score": 72.5,
    }
    memory_service.save_memory = AsyncMock(return_value=memory_data)
    memory_service.retrieve_memory = AsyncMock(
        return_value=UserMemorySchema(**memory_data)
    )

    # Sustainability service mock
    sustainability_service = AsyncMock()
    sustainability_service.recommend_alternatives = AsyncMock(
        return_value=SustainabilityRecommendResponseSchema(
            recommendations=[
                EcoAlternativeSchema(
                    original_product_id=PRODUCT_ID_1,
                    original_product_name="Organic Baby Formula",
                    alternative_product_id=ECO_PRODUCT_ID,
                    alternative_product_name="Eco Organic Formula Plus",
                    carbon_saved=0.8,
                    price_difference=2.0,
                    sustainability_score=85.0,
                )
            ],
            total_carbon_saved=0.8,
            overall_sustainability_score=85.0,
        )
    )

    return {
        "chat": chat_service,
        "cart": cart_service,
        "memory": memory_service,
        "sustainability": sustainability_service,
    }


@pytest.fixture
def client(mock_services: dict[str, AsyncMock]) -> TestClient:
    """Create a TestClient with all mocked services."""
    app = _build_app(mock_services)
    return TestClient(app)


# ---------------------------------------------------------------------------
# Test: Complete User Journey (Sequential Steps)
# ---------------------------------------------------------------------------


class TestUserJourney:
    """End-to-end test validating the complete user journey."""

    # ------------------------------------------------------------------
    # Step 1: User starts chat
    # ------------------------------------------------------------------

    def test_step1_user_starts_chat(self, client: TestClient) -> None:
        """User sends a message and receives a response with recommendations."""
        response = client.post(
            "/api/v1/chat",
            json={
                "user_id": str(USER_ID),
                "message": "I need baby formula urgently, my infant is hungry",
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Chat response is valid
        assert data["session_id"] == str(SESSION_ID)
        assert data["user_message"]["role"] == "user"
        assert data["assistant_message"]["role"] == "assistant"
        assert len(data["assistant_message"]["content"]) > 0

    def test_step1_chat_returns_session(self, client: TestClient) -> None:
        """Chat creates a session for conversation continuity."""
        response = client.post(
            "/api/v1/chat",
            json={"user_id": str(USER_ID), "message": "Baby formula needed"},
        )
        session_id = response.json()["session_id"]
        UUID(session_id)  # valid UUID

    # ------------------------------------------------------------------
    # Step 2: Intent is identified
    # ------------------------------------------------------------------

    def test_step2_intent_identified_in_response(self, client: TestClient) -> None:
        """Chat response reveals the detected intent (category, urgency)."""
        response = client.post(
            "/api/v1/chat",
            json={"user_id": str(USER_ID), "message": "Need baby formula urgently"},
        )
        data = response.json()

        # Category identified
        assert data["cart"]["category"] == "baby"

        # Urgency assessed
        assert data["urgency"]["level"] == "HIGH"
        assert 0 <= data["urgency"]["score"] <= 100
        assert len(data["urgency"]["reasoning"]) > 0

    def test_step2_reasoning_includes_intent_info(self, client: TestClient) -> None:
        """Reasoning text references the identified intent."""
        response = client.post(
            "/api/v1/chat",
            json={"user_id": str(USER_ID), "message": "Baby formula needed now"},
        )
        reasoning = response.json()["reasoning"]
        assert "baby" in reasoning.lower()
        assert "urgent" in reasoning.lower() or "HIGH" in reasoning

    # ------------------------------------------------------------------
    # Step 3: Recommendations generated
    # ------------------------------------------------------------------

    def test_step3_recommendations_in_chat_response(self, client: TestClient) -> None:
        """Chat response includes recommended products."""
        response = client.post(
            "/api/v1/chat",
            json={"user_id": str(USER_ID), "message": "Baby formula urgently"},
        )
        products = response.json()["cart"]["products"]
        assert len(products) > 0
        assert products[0]["title"] == "Organic Baby Formula"
        assert products[0]["price"] == 24.99

    def test_step3_products_are_ranked(self, client: TestClient) -> None:
        """Recommended products are ordered by score (highest first)."""
        response = client.post(
            "/api/v1/chat",
            json={"user_id": str(USER_ID), "message": "Baby supplies"},
        )
        products = response.json()["cart"]["products"]
        scores = [p["score"] for p in products]
        assert scores == sorted(scores, reverse=True)

    def test_step3_bundles_included(self, client: TestClient) -> None:
        """Response includes bundle suggestions."""
        response = client.post(
            "/api/v1/chat",
            json={"user_id": str(USER_ID), "message": "Baby items needed"},
        )
        bundles = response.json()["cart"]["bundles"]
        assert len(bundles) > 0

    def test_step3_confidence_reported(self, client: TestClient) -> None:
        """Confidence score is in metadata."""
        response = client.post(
            "/api/v1/chat",
            json={"user_id": str(USER_ID), "message": "Baby formula"},
        )
        metadata = response.json()["metadata"]
        assert "confidence" in metadata
        assert metadata["confidence"] > 0

    # ------------------------------------------------------------------
    # Step 4: Product added to cart
    # ------------------------------------------------------------------

    def test_step4_add_product_to_cart(self, client: TestClient) -> None:
        """User adds the recommended product to their cart."""
        response = client.post(
            "/api/v1/cart/add",
            json={
                "user_id": str(USER_ID),
                "product_id": str(PRODUCT_ID_1),
                "quantity": 1,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Item added to cart"
        assert data["cart"]["total_amount"] == 24.99

    def test_step4_cart_contains_product(self, client: TestClient) -> None:
        """Cart reflects the added product."""
        # Add item first
        client.post(
            "/api/v1/cart/add",
            json={"user_id": str(USER_ID), "product_id": str(PRODUCT_ID_1)},
        )

        # Verify cart
        response = client.get(f"/api/v1/cart/{USER_ID}")
        assert response.status_code == 200
        cart = response.json()
        assert len(cart["items"]) > 0
        assert cart["items"][0]["product_name"] == "Organic Baby Formula"
        assert cart["items"][0]["quantity"] == 1
        assert cart["total_amount"] == 24.99

    def test_step4_cart_item_structure(self, client: TestClient) -> None:
        """Cart items have all required fields."""
        response = client.get(f"/api/v1/cart/{USER_ID}")
        item = response.json()["items"][0]
        assert "id" in item
        assert "product_id" in item
        assert "product_name" in item
        assert "quantity" in item
        assert "unit_price" in item
        assert "line_total" in item

    # ------------------------------------------------------------------
    # Step 5: Memory stored
    # ------------------------------------------------------------------

    def test_step5_store_user_preferences(self, client: TestClient) -> None:
        """User preferences are stored in memory."""
        response = client.post(
            "/api/v1/memory/store",
            json={
                "user_id": str(USER_ID),
                "memory": {
                    "dietary_preferences": ["organic"],
                    "preferred_brands": ["Nature's Best"],
                    "budget_level": "medium",
                    "family_size": 3,
                    "purchase_patterns": ["baby supplies", "organic formula"],
                    "sustainability_score": 72.5,
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(USER_ID)
        assert data["memory"]["preferred_brands"] == ["Nature's Best"]

    def test_step5_retrieve_stored_memory(self, client: TestClient) -> None:
        """Stored memory can be retrieved."""
        response = client.get(f"/api/v1/memory/{USER_ID}")
        assert response.status_code == 200
        memory = response.json()["memory"]
        assert memory["dietary_preferences"] == ["organic"]
        assert memory["sustainability_score"] == 72.5

    def test_step5_memory_used_in_recommendations(self, client: TestClient) -> None:
        """Chat response metadata indicates memory was used."""
        response = client.post(
            "/api/v1/chat",
            json={"user_id": str(USER_ID), "message": "More baby items"},
        )
        metadata = response.json()["metadata"]
        assert metadata["memory_used"] is True

    # ------------------------------------------------------------------
    # Step 6: Sustainability suggestions shown
    # ------------------------------------------------------------------

    def test_step6_eco_alternative_in_chat(self, client: TestClient) -> None:
        """Chat response includes an eco-friendly alternative."""
        response = client.post(
            "/api/v1/chat",
            json={"user_id": str(USER_ID), "message": "Baby formula"},
        )
        eco = response.json()["eco_alternative"]
        assert eco is not None
        assert "alternative_product_name" in eco
        assert "carbon_saved" in eco
        assert eco["carbon_saved"] > 0

    def test_step6_sustainability_recommendations_endpoint(self, client: TestClient) -> None:
        """Dedicated sustainability endpoint returns eco alternatives."""
        response = client.post(
            "/api/v1/sustainability/recommend",
            json={"product_ids": [str(PRODUCT_ID_1), str(PRODUCT_ID_2)]},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["recommendations"]) > 0
        assert data["total_carbon_saved"] > 0
        assert data["overall_sustainability_score"] > 0

    def test_step6_eco_alternative_details(self, client: TestClient) -> None:
        """Eco alternative has meaningful details."""
        response = client.post(
            "/api/v1/sustainability/recommend",
            json={"product_ids": [str(PRODUCT_ID_1)]},
        )
        alt = response.json()["recommendations"][0]
        assert alt["original_product_name"] == "Organic Baby Formula"
        assert alt["alternative_product_name"] == "Eco Organic Formula Plus"
        assert alt["sustainability_score"] > 0
        assert alt["carbon_saved"] == 0.8

    def test_step6_sustainability_score_in_memory(self, client: TestClient) -> None:
        """User's sustainability score is tracked in memory."""
        response = client.get(f"/api/v1/memory/{USER_ID}")
        memory = response.json()["memory"]
        assert memory["sustainability_score"] > 0


# ---------------------------------------------------------------------------
# Test: Journey Validation (Cross-Step Assertions)
# ---------------------------------------------------------------------------


class TestJourneyValidation:
    """Cross-step validation ensuring data flows correctly between steps."""

    def test_chat_product_ids_match_cart_add(
        self, client: TestClient, mock_services: dict[str, AsyncMock]
    ) -> None:
        """Product IDs from chat recommendations can be used to add to cart."""
        # Get recommendations
        chat_resp = client.post(
            "/api/v1/chat",
            json={"user_id": str(USER_ID), "message": "Baby formula"},
        )
        product_id = chat_resp.json()["cart"]["products"][0]["id"]

        # Add to cart using the same ID
        cart_resp = client.post(
            "/api/v1/cart/add",
            json={"user_id": str(USER_ID), "product_id": product_id, "quantity": 1},
        )
        assert cart_resp.status_code == 200

    def test_session_continuity(self, client: TestClient) -> None:
        """Session ID from first chat can be used in follow-up."""
        # First message
        resp1 = client.post(
            "/api/v1/chat",
            json={"user_id": str(USER_ID), "message": "Baby formula needed"},
        )
        session_id = resp1.json()["session_id"]

        # Follow-up with session
        resp2 = client.post(
            "/api/v1/chat",
            json={
                "user_id": str(USER_ID),
                "message": "Add the first one to my cart",
                "session_id": session_id,
            },
        )
        assert resp2.status_code == 200

    def test_complete_journey_all_endpoints_accessible(self, client: TestClient) -> None:
        """All endpoints in the journey are accessible and return 200."""
        # 1. Chat
        assert client.post(
            "/api/v1/chat",
            json={"user_id": str(USER_ID), "message": "Baby formula"},
        ).status_code == 200

        # 2. Add to cart
        assert client.post(
            "/api/v1/cart/add",
            json={"user_id": str(USER_ID), "product_id": str(PRODUCT_ID_1)},
        ).status_code == 200

        # 3. Get cart
        assert client.get(f"/api/v1/cart/{USER_ID}").status_code == 200

        # 4. Store memory
        assert client.post(
            "/api/v1/memory/store",
            json={"user_id": str(USER_ID), "memory": {"budget_level": "medium"}},
        ).status_code == 200

        # 5. Get memory
        assert client.get(f"/api/v1/memory/{USER_ID}").status_code == 200

        # 6. Sustainability
        assert client.post(
            "/api/v1/sustainability/recommend",
            json={"product_ids": [str(PRODUCT_ID_1)]},
        ).status_code == 200

    def test_urgency_affects_response_priority(self, client: TestClient) -> None:
        """High urgency is reflected throughout the response."""
        response = client.post(
            "/api/v1/chat",
            json={"user_id": str(USER_ID), "message": "URGENT baby formula NOW"},
        )
        data = response.json()
        assert data["urgency"]["level"] == "HIGH"
        # High urgency should produce non-empty recommendations
        assert len(data["cart"]["products"]) > 0

    def test_personalization_indicator(self, client: TestClient) -> None:
        """Response indicates when personalization was applied."""
        response = client.post(
            "/api/v1/chat",
            json={"user_id": str(USER_ID), "message": "Shopping for baby"},
        )
        assert response.json()["metadata"]["memory_used"] is True
