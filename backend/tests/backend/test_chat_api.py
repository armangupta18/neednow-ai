"""Tests for the Chat API endpoint (app/api/v1/chat.py).

Covers:
    1. Successful chat request and response schema validation.
    2. Invalid request body (missing required fields).
    3. Empty/blank message validation.
    4. Service exception handling (ValueError, PermissionError, RuntimeError).
    5. Response schema structure validation.

Uses a self-contained FastAPI app to avoid deep import chains from the
agent modules. The chat router is replicated with the same interface
and dependency-injected mock ChatService.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Lightweight schema replicas (avoids deep agent import chains)
# ---------------------------------------------------------------------------


class AgentMessageSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    session_id: UUID
    content: str = Field(..., min_length=1)
    role: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    user_id: UUID
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: UUID | None = None
    context: dict[str, Any] | None = None

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message must contain non-whitespace characters")
        return v.strip()


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
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatHistoryResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    user_id: UUID
    messages: list[AgentMessageSchema] = Field(default_factory=list)
    total_messages: int = 0
    has_more: bool = False


# ---------------------------------------------------------------------------
# Simulated exceptions (mirrors app.agents.shared.base_agent)
# ---------------------------------------------------------------------------


class AgentValidationError(Exception):
    pass


class AgentExecutionError(Exception):
    pass


# ---------------------------------------------------------------------------
# Test Router (replicates app/api/v1/chat.py interface)
# ---------------------------------------------------------------------------


def _build_chat_router(get_service_dep):
    """Build a chat router with the given dependency."""
    router = APIRouter(prefix="/chat", tags=["Chat"])

    @router.post("", response_model=ChatResponseSchema, status_code=200)
    async def send_chat_message(
        request: ChatRequestSchema,
        chat_service=Depends(get_service_dep),
    ) -> ChatResponseSchema:
        try:
            return await chat_service.process_message(request)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except AgentValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except AgentExecutionError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to process chat message")

    @router.get("/{session_id}/history", response_model=ChatHistoryResponseSchema, status_code=200)
    async def get_chat_history(
        session_id: UUID,
        user_id: UUID,
        chat_service=Depends(get_service_dep),
    ) -> ChatHistoryResponseSchema:
        try:
            return chat_service.get_history(session_id=session_id, user_id=user_id)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to retrieve chat history")

    return router


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def user_id() -> UUID:
    return uuid4()


@pytest.fixture
def session_id() -> UUID:
    return uuid4()


@pytest.fixture
def mock_chat_response(user_id: UUID, session_id: UUID) -> ChatResponseSchema:
    """Create a realistic ChatResponse for mocking."""
    return ChatResponseSchema(
        session_id=session_id,
        user_message=AgentMessageSchema(
            user_id=user_id,
            session_id=session_id,
            content="I need baby formula urgently",
            role="user",
        ),
        assistant_message=AgentMessageSchema(
            user_id=user_id,
            session_id=session_id,
            content="I found several baby formula options for you.",
            role="assistant",
            metadata={"urgency_level": "high", "confidence": 0.92},
        ),
        cart={"cart_id": str(uuid4()), "total_amount": 0.0, "item_count": 0, "items": []},
        urgency={"level": "high", "score": 0.85, "reasoning": "User mentioned urgently"},
        reasoning="User needs baby formula urgently. Routing to product search.",
        eco_alternative={
            "product_name": "Organic Baby Formula",
            "eco_score": 78.5,
            "carbon_saved_kg": 0.3,
            "reason": "Made with sustainably sourced ingredients",
        },
        metadata={"pipeline_time_ms": 245.3, "agents_invoked": ["intent", "urgency", "product"]},
    )


@pytest.fixture
def mock_chat_service(mock_chat_response: ChatResponseSchema, session_id: UUID, user_id: UUID) -> AsyncMock:
    """Create a mocked ChatService."""
    service = AsyncMock()
    service.process_message = AsyncMock(return_value=mock_chat_response)
    service.get_history = MagicMock(
        return_value=ChatHistoryResponseSchema(
            session_id=session_id,
            user_id=user_id,
            messages=[],
            total_messages=0,
            has_more=False,
        )
    )
    return service


@pytest.fixture
def client(mock_chat_service: AsyncMock) -> TestClient:
    """Create a TestClient with the mocked chat service."""
    app = FastAPI()

    def get_service():
        return mock_chat_service

    router = _build_chat_router(get_service)
    app.include_router(router, prefix="/api/v1")

    return TestClient(app)


@pytest.fixture
def valid_payload() -> dict[str, Any]:
    """A valid chat request payload."""
    return {
        "user_id": str(uuid4()),
        "message": "I need baby formula urgently",
    }


# ---------------------------------------------------------------------------
# Test 1: Chat Request Success
# ---------------------------------------------------------------------------


class TestChatRequestSuccess:
    """Test successful chat message processing."""

    def test_send_message_returns_200(
        self, client: TestClient, valid_payload: dict[str, Any]
    ) -> None:
        response = client.post("/api/v1/chat", json=valid_payload)
        assert response.status_code == 200

    def test_send_message_returns_valid_json(
        self, client: TestClient, valid_payload: dict[str, Any]
    ) -> None:
        response = client.post("/api/v1/chat", json=valid_payload)
        data = response.json()

        assert "session_id" in data
        assert "user_message" in data
        assert "assistant_message" in data
        assert "cart" in data
        assert "urgency" in data
        assert "reasoning" in data

    def test_send_message_with_session_id(
        self, client: TestClient, valid_payload: dict[str, Any]
    ) -> None:
        valid_payload["session_id"] = str(uuid4())
        response = client.post("/api/v1/chat", json=valid_payload)
        assert response.status_code == 200

    def test_service_called_with_request(
        self,
        client: TestClient,
        valid_payload: dict[str, Any],
        mock_chat_service: AsyncMock,
    ) -> None:
        client.post("/api/v1/chat", json=valid_payload)
        mock_chat_service.process_message.assert_called_once()

        call_args = mock_chat_service.process_message.call_args[0][0]
        assert isinstance(call_args, ChatRequestSchema)
        assert str(call_args.user_id) == valid_payload["user_id"]
        assert call_args.message == valid_payload["message"]

    def test_message_is_stripped(
        self, client: TestClient, mock_chat_service: AsyncMock
    ) -> None:
        payload = {"user_id": str(uuid4()), "message": "  hello world  "}
        client.post("/api/v1/chat", json=payload)

        call_args = mock_chat_service.process_message.call_args[0][0]
        assert call_args.message == "hello world"


# ---------------------------------------------------------------------------
# Test 2: Invalid Request Body
# ---------------------------------------------------------------------------


class TestInvalidRequestBody:
    """Test validation of malformed request bodies."""

    def test_missing_user_id_returns_422(self, client: TestClient) -> None:
        response = client.post("/api/v1/chat", json={"message": "Hello"})
        assert response.status_code == 422

    def test_missing_message_returns_422(self, client: TestClient) -> None:
        response = client.post("/api/v1/chat", json={"user_id": str(uuid4())})
        assert response.status_code == 422

    def test_invalid_user_id_format_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/chat",
            json={"user_id": "not-a-uuid", "message": "Hello"},
        )
        assert response.status_code == 422

    def test_invalid_session_id_format_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/chat",
            json={
                "user_id": str(uuid4()),
                "message": "Hello",
                "session_id": "invalid",
            },
        )
        assert response.status_code == 422

    def test_extra_fields_rejected(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/chat",
            json={
                "user_id": str(uuid4()),
                "message": "Hello",
                "unexpected_field": "value",
            },
        )
        assert response.status_code == 422

    def test_empty_body_returns_422(self, client: TestClient) -> None:
        response = client.post("/api/v1/chat", json={})
        assert response.status_code == 422

    def test_non_json_body_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/chat",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Test 3: Empty Message Validation
# ---------------------------------------------------------------------------


class TestEmptyMessageValidation:
    """Test that empty/blank messages are rejected."""

    def test_empty_string_message_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/chat",
            json={"user_id": str(uuid4()), "message": ""},
        )
        assert response.status_code == 422

    def test_whitespace_only_message_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/chat",
            json={"user_id": str(uuid4()), "message": "   \t\n  "},
        )
        assert response.status_code == 422

    def test_message_exceeds_max_length_returns_422(self, client: TestClient) -> None:
        long_message = "x" * 5001
        response = client.post(
            "/api/v1/chat",
            json={"user_id": str(uuid4()), "message": long_message},
        )
        assert response.status_code == 422

    def test_single_character_message_accepted(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/chat",
            json={"user_id": str(uuid4()), "message": "?"},
        )
        assert response.status_code == 200

    def test_max_length_message_accepted(self, client: TestClient) -> None:
        message = "a" * 5000
        response = client.post(
            "/api/v1/chat",
            json={"user_id": str(uuid4()), "message": message},
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Test 4: Service Exception Handling
# ---------------------------------------------------------------------------


class TestServiceExceptionHandling:
    """Test that service-layer exceptions map to correct HTTP status codes."""

    def test_value_error_returns_400(
        self, client: TestClient, valid_payload: dict[str, Any], mock_chat_service: AsyncMock
    ) -> None:
        mock_chat_service.process_message.side_effect = ValueError("Invalid input")
        response = client.post("/api/v1/chat", json=valid_payload)
        assert response.status_code == 400
        assert "Invalid input" in response.json()["detail"]

    def test_permission_error_returns_403(
        self, client: TestClient, valid_payload: dict[str, Any], mock_chat_service: AsyncMock
    ) -> None:
        mock_chat_service.process_message.side_effect = PermissionError("Access denied")
        response = client.post("/api/v1/chat", json=valid_payload)
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]

    def test_unexpected_exception_returns_500(
        self, client: TestClient, valid_payload: dict[str, Any], mock_chat_service: AsyncMock
    ) -> None:
        mock_chat_service.process_message.side_effect = RuntimeError("Unexpected failure")
        response = client.post("/api/v1/chat", json=valid_payload)
        assert response.status_code == 500
        assert "Failed to process chat message" in response.json()["detail"]

    def test_agent_validation_error_returns_422(
        self, client: TestClient, valid_payload: dict[str, Any], mock_chat_service: AsyncMock
    ) -> None:
        mock_chat_service.process_message.side_effect = AgentValidationError("Bad agent input")
        response = client.post("/api/v1/chat", json=valid_payload)
        assert response.status_code == 422
        assert "Bad agent input" in response.json()["detail"]

    def test_agent_execution_error_returns_422(
        self, client: TestClient, valid_payload: dict[str, Any], mock_chat_service: AsyncMock
    ) -> None:
        mock_chat_service.process_message.side_effect = AgentExecutionError("Agent crashed")
        response = client.post("/api/v1/chat", json=valid_payload)
        assert response.status_code == 422
        assert "Agent crashed" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Test 5: Response Schema Validation
# ---------------------------------------------------------------------------


class TestResponseSchemaValidation:
    """Test that the response conforms to the ChatResponse schema."""

    def test_response_has_session_id_uuid(
        self, client: TestClient, valid_payload: dict[str, Any]
    ) -> None:
        response = client.post("/api/v1/chat", json=valid_payload)
        data = response.json()
        UUID(data["session_id"])  # Raises if invalid

    def test_response_user_message_structure(
        self, client: TestClient, valid_payload: dict[str, Any]
    ) -> None:
        response = client.post("/api/v1/chat", json=valid_payload)
        user_msg = response.json()["user_message"]

        assert "user_id" in user_msg
        assert "session_id" in user_msg
        assert "content" in user_msg
        assert "role" in user_msg
        assert user_msg["role"] == "user"

    def test_response_assistant_message_structure(
        self, client: TestClient, valid_payload: dict[str, Any]
    ) -> None:
        response = client.post("/api/v1/chat", json=valid_payload)
        assistant_msg = response.json()["assistant_message"]

        assert "user_id" in assistant_msg
        assert "session_id" in assistant_msg
        assert "content" in assistant_msg
        assert "role" in assistant_msg
        assert assistant_msg["role"] == "assistant"
        assert len(assistant_msg["content"]) > 0

    def test_response_cart_is_dict(
        self, client: TestClient, valid_payload: dict[str, Any]
    ) -> None:
        response = client.post("/api/v1/chat", json=valid_payload)
        assert isinstance(response.json()["cart"], dict)

    def test_response_urgency_has_level_and_score(
        self, client: TestClient, valid_payload: dict[str, Any]
    ) -> None:
        response = client.post("/api/v1/chat", json=valid_payload)
        urgency = response.json()["urgency"]
        assert "level" in urgency
        assert "score" in urgency

    def test_response_reasoning_is_non_empty_string(
        self, client: TestClient, valid_payload: dict[str, Any]
    ) -> None:
        response = client.post("/api/v1/chat", json=valid_payload)
        reasoning = response.json()["reasoning"]
        assert isinstance(reasoning, str)
        assert len(reasoning) > 0

    def test_response_eco_alternative_nullable(
        self,
        client: TestClient,
        valid_payload: dict[str, Any],
        mock_chat_service: AsyncMock,
        mock_chat_response: ChatResponseSchema,
    ) -> None:
        modified = mock_chat_response.model_copy(update={"eco_alternative": None})
        mock_chat_service.process_message.return_value = modified

        response = client.post("/api/v1/chat", json=valid_payload)
        assert response.json()["eco_alternative"] is None

    def test_response_metadata_is_dict(
        self, client: TestClient, valid_payload: dict[str, Any]
    ) -> None:
        response = client.post("/api/v1/chat", json=valid_payload)
        assert isinstance(response.json()["metadata"], dict)

    def test_full_response_deserializes_to_schema(
        self, client: TestClient, valid_payload: dict[str, Any]
    ) -> None:
        response = client.post("/api/v1/chat", json=valid_payload)
        data = response.json()
        parsed = ChatResponseSchema.model_validate(data)
        assert parsed.session_id is not None
        assert parsed.reasoning != ""


# ---------------------------------------------------------------------------
# Test: Chat History Endpoint
# ---------------------------------------------------------------------------


class TestChatHistoryEndpoint:
    """Test the GET /chat/{session_id}/history endpoint."""

    def test_get_history_returns_200(self, client: TestClient) -> None:
        response = client.get(
            f"/api/v1/chat/{uuid4()}/history",
            params={"user_id": str(uuid4())},
        )
        assert response.status_code == 200

    def test_get_history_response_structure(self, client: TestClient) -> None:
        response = client.get(
            f"/api/v1/chat/{uuid4()}/history",
            params={"user_id": str(uuid4())},
        )
        data = response.json()

        assert "session_id" in data
        assert "user_id" in data
        assert "messages" in data
        assert isinstance(data["messages"], list)

    def test_get_history_invalid_session_id_returns_422(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/chat/not-a-uuid/history",
            params={"user_id": str(uuid4())},
        )
        assert response.status_code == 422

    def test_get_history_permission_error_returns_403(
        self, client: TestClient, mock_chat_service: AsyncMock
    ) -> None:
        mock_chat_service.get_history.side_effect = PermissionError("Not your session")
        response = client.get(
            f"/api/v1/chat/{uuid4()}/history",
            params={"user_id": str(uuid4())},
        )
        assert response.status_code == 403
