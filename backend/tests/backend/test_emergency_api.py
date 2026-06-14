"""Tests for the Emergency API endpoint (app/api/v1/emergency.py).

Covers:
    1. Urgency analysis — POST /analyze.
    2. Emergency escalation — POST /escalate.
    3. Health endpoint — GET /health.
    4. Invalid payload — validation errors and error handling.

Uses a self-contained FastAPI app to avoid deep import chains.
The emergency router interface is replicated with a mocked service.
"""

from __future__ import annotations

from enum import Enum
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Lightweight schema replicas
# ---------------------------------------------------------------------------


class UrgencyLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class EmergencyAnalyzeRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    user_id: UUID
    text: str = Field(..., min_length=1, max_length=5000)
    user_context: dict[str, Any] = Field(default_factory=dict)


class EmergencyAnalyzeResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: UUID
    urgency: UrgencyLevel
    score: int = Field(ge=0, le=100)
    explanation: str
    is_emergency: bool
    escalation_recommended: bool


class EmergencyEscalateRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    user_id: UUID
    text: str = Field(..., min_length=1, max_length=5000)
    user_context: dict[str, Any] = Field(default_factory=dict)
    contact_phone: str | None = Field(default=None, max_length=30)


class EmergencyEscalateResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: UUID
    escalated: bool
    urgency: UrgencyLevel
    score: int = Field(ge=0, le=100)
    workflow_id: str
    message: str
    actions: list[str] = Field(default_factory=list)


class EmergencyHealthResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
    urgency_agent: str
    emergency_agent: str


# ---------------------------------------------------------------------------
# Simulated exceptions
# ---------------------------------------------------------------------------


class UrgencyAgentException(Exception):
    pass


# ---------------------------------------------------------------------------
# Test Router (replicates app/api/v1/emergency.py interface)
# ---------------------------------------------------------------------------


def _build_emergency_router(get_service_dep):
    """Build an emergency router with the given dependency."""
    router = APIRouter(prefix="/emergency", tags=["Emergency"])

    @router.post("/analyze", response_model=EmergencyAnalyzeResponseSchema, status_code=200)
    async def analyze_emergency(
        request: EmergencyAnalyzeRequestSchema,
        service=Depends(get_service_dep),
    ) -> EmergencyAnalyzeResponseSchema:
        try:
            return await service.analyze_urgency(
                user_id=request.user_id,
                text=request.text,
                user_context=request.user_context or None,
            )
        except UrgencyAgentException as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to analyze emergency urgency")

    @router.post("/escalate", response_model=EmergencyEscalateResponseSchema, status_code=200)
    async def escalate_emergency(
        request: EmergencyEscalateRequestSchema,
        service=Depends(get_service_dep),
    ) -> EmergencyEscalateResponseSchema:
        try:
            return await service.escalate_emergency(
                user_id=request.user_id,
                text=request.text,
                user_context=request.user_context or None,
                contact_phone=request.contact_phone,
            )
        except UrgencyAgentException as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to escalate emergency workflow")

    @router.get("/health", response_model=EmergencyHealthResponseSchema, status_code=200)
    async def emergency_health(
        service=Depends(get_service_dep),
    ) -> EmergencyHealthResponseSchema:
        try:
            return service.health_check()
        except Exception:
            raise HTTPException(status_code=503, detail="Emergency subsystem unavailable")

    return router


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def user_id() -> UUID:
    return uuid4()


@pytest.fixture
def sample_analyze_response(user_id: UUID) -> EmergencyAnalyzeResponseSchema:
    """Sample urgency analysis result."""
    return EmergencyAnalyzeResponseSchema(
        user_id=user_id,
        urgency=UrgencyLevel.HIGH,
        score=78,
        explanation="User described a time-sensitive medical need for a child.",
        is_emergency=True,
        escalation_recommended=True,
    )


@pytest.fixture
def sample_escalate_response(user_id: UUID) -> EmergencyEscalateResponseSchema:
    """Sample escalation result."""
    return EmergencyEscalateResponseSchema(
        user_id=user_id,
        escalated=True,
        urgency=UrgencyLevel.CRITICAL,
        score=95,
        workflow_id="wf_abc123",
        message="Emergency workflow triggered. Priority delivery activated.",
        actions=["priority_delivery", "notify_support", "waive_fees"],
    )


@pytest.fixture
def sample_health_response() -> EmergencyHealthResponseSchema:
    """Sample health check response."""
    return EmergencyHealthResponseSchema(
        status="healthy",
        urgency_agent="operational",
        emergency_agent="operational",
    )


@pytest.fixture
def mock_emergency_service(
    sample_analyze_response: EmergencyAnalyzeResponseSchema,
    sample_escalate_response: EmergencyEscalateResponseSchema,
    sample_health_response: EmergencyHealthResponseSchema,
) -> AsyncMock:
    """Create a mocked EmergencyService."""
    service = AsyncMock()
    service.analyze_urgency = AsyncMock(return_value=sample_analyze_response)
    service.escalate_emergency = AsyncMock(return_value=sample_escalate_response)
    service.health_check = MagicMock(return_value=sample_health_response)
    return service


@pytest.fixture
def client(mock_emergency_service: AsyncMock) -> TestClient:
    """Create a TestClient with the mocked emergency service."""
    app = FastAPI()

    def get_service():
        return mock_emergency_service

    router = _build_emergency_router(get_service)
    app.include_router(router, prefix="/api/v1")

    return TestClient(app)


@pytest.fixture
def valid_analyze_payload(user_id: UUID) -> dict[str, Any]:
    """Valid analyze request payload."""
    return {
        "user_id": str(user_id),
        "text": "My baby needs formula urgently, she hasn't eaten in hours",
    }


@pytest.fixture
def valid_escalate_payload(user_id: UUID) -> dict[str, Any]:
    """Valid escalate request payload."""
    return {
        "user_id": str(user_id),
        "text": "Medical emergency — need insulin delivered immediately",
        "contact_phone": "+1234567890",
    }


# ---------------------------------------------------------------------------
# Test 1: Urgency Analysis
# ---------------------------------------------------------------------------


class TestUrgencyAnalysis:
    """Test POST /api/v1/emergency/analyze endpoint."""

    def test_analyze_returns_200(
        self, client: TestClient, valid_analyze_payload: dict[str, Any]
    ) -> None:
        """Successful analysis returns 200."""
        response = client.post("/api/v1/emergency/analyze", json=valid_analyze_payload)
        assert response.status_code == 200

    def test_analyze_returns_user_id(
        self, client: TestClient, valid_analyze_payload: dict[str, Any]
    ) -> None:
        """Response contains the correct user_id."""
        response = client.post("/api/v1/emergency/analyze", json=valid_analyze_payload)
        data = response.json()
        assert data["user_id"] == valid_analyze_payload["user_id"]

    def test_analyze_returns_urgency_level(
        self, client: TestClient, valid_analyze_payload: dict[str, Any]
    ) -> None:
        """Response contains a valid urgency level."""
        response = client.post("/api/v1/emergency/analyze", json=valid_analyze_payload)
        data = response.json()
        assert data["urgency"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

    def test_analyze_returns_score_in_range(
        self, client: TestClient, valid_analyze_payload: dict[str, Any]
    ) -> None:
        """Score is between 0 and 100."""
        response = client.post("/api/v1/emergency/analyze", json=valid_analyze_payload)
        score = response.json()["score"]
        assert 0 <= score <= 100

    def test_analyze_returns_explanation(
        self, client: TestClient, valid_analyze_payload: dict[str, Any]
    ) -> None:
        """Response contains a non-empty explanation."""
        response = client.post("/api/v1/emergency/analyze", json=valid_analyze_payload)
        explanation = response.json()["explanation"]
        assert isinstance(explanation, str)
        assert len(explanation) > 0

    def test_analyze_returns_is_emergency_boolean(
        self, client: TestClient, valid_analyze_payload: dict[str, Any]
    ) -> None:
        """is_emergency is a boolean."""
        response = client.post("/api/v1/emergency/analyze", json=valid_analyze_payload)
        assert isinstance(response.json()["is_emergency"], bool)

    def test_analyze_returns_escalation_recommended(
        self, client: TestClient, valid_analyze_payload: dict[str, Any]
    ) -> None:
        """escalation_recommended is a boolean."""
        response = client.post("/api/v1/emergency/analyze", json=valid_analyze_payload)
        assert isinstance(response.json()["escalation_recommended"], bool)

    def test_analyze_calls_service(
        self,
        client: TestClient,
        valid_analyze_payload: dict[str, Any],
        mock_emergency_service: AsyncMock,
    ) -> None:
        """Service.analyze_urgency is called with correct args."""
        client.post("/api/v1/emergency/analyze", json=valid_analyze_payload)
        mock_emergency_service.analyze_urgency.assert_called_once()
        call_kwargs = mock_emergency_service.analyze_urgency.call_args[1]
        assert str(call_kwargs["user_id"]) == valid_analyze_payload["user_id"]
        assert call_kwargs["text"] == valid_analyze_payload["text"]

    def test_analyze_with_user_context(
        self, client: TestClient, user_id: UUID, mock_emergency_service: AsyncMock
    ) -> None:
        """User context is passed to the service."""
        payload = {
            "user_id": str(user_id),
            "text": "Need help now",
            "user_context": {"location": "home", "has_children": True},
        }
        client.post("/api/v1/emergency/analyze", json=payload)
        call_kwargs = mock_emergency_service.analyze_urgency.call_args[1]
        assert call_kwargs["user_context"] == {"location": "home", "has_children": True}

    def test_analyze_response_schema(
        self, client: TestClient, valid_analyze_payload: dict[str, Any]
    ) -> None:
        """Response deserializes into EmergencyAnalyzeResponseSchema."""
        response = client.post("/api/v1/emergency/analyze", json=valid_analyze_payload)
        parsed = EmergencyAnalyzeResponseSchema.model_validate(response.json())
        assert parsed.urgency == UrgencyLevel.HIGH
        assert parsed.score == 78


# ---------------------------------------------------------------------------
# Test 2: Emergency Escalation
# ---------------------------------------------------------------------------


class TestEmergencyEscalation:
    """Test POST /api/v1/emergency/escalate endpoint."""

    def test_escalate_returns_200(
        self, client: TestClient, valid_escalate_payload: dict[str, Any]
    ) -> None:
        """Successful escalation returns 200."""
        response = client.post("/api/v1/emergency/escalate", json=valid_escalate_payload)
        assert response.status_code == 200

    def test_escalate_returns_escalated_true(
        self, client: TestClient, valid_escalate_payload: dict[str, Any]
    ) -> None:
        """Response has escalated=True."""
        response = client.post("/api/v1/emergency/escalate", json=valid_escalate_payload)
        assert response.json()["escalated"] is True

    def test_escalate_returns_workflow_id(
        self, client: TestClient, valid_escalate_payload: dict[str, Any]
    ) -> None:
        """Response contains a workflow_id."""
        response = client.post("/api/v1/emergency/escalate", json=valid_escalate_payload)
        data = response.json()
        assert "workflow_id" in data
        assert len(data["workflow_id"]) > 0

    def test_escalate_returns_urgency_level(
        self, client: TestClient, valid_escalate_payload: dict[str, Any]
    ) -> None:
        """Response contains a valid urgency level."""
        response = client.post("/api/v1/emergency/escalate", json=valid_escalate_payload)
        assert response.json()["urgency"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

    def test_escalate_returns_actions_list(
        self, client: TestClient, valid_escalate_payload: dict[str, Any]
    ) -> None:
        """Response contains an actions list."""
        response = client.post("/api/v1/emergency/escalate", json=valid_escalate_payload)
        actions = response.json()["actions"]
        assert isinstance(actions, list)
        assert len(actions) > 0

    def test_escalate_returns_message(
        self, client: TestClient, valid_escalate_payload: dict[str, Any]
    ) -> None:
        """Response contains a human-readable message."""
        response = client.post("/api/v1/emergency/escalate", json=valid_escalate_payload)
        message = response.json()["message"]
        assert isinstance(message, str)
        assert len(message) > 0

    def test_escalate_with_contact_phone(
        self, client: TestClient, valid_escalate_payload: dict[str, Any], mock_emergency_service: AsyncMock
    ) -> None:
        """Contact phone is passed to the service."""
        client.post("/api/v1/emergency/escalate", json=valid_escalate_payload)
        call_kwargs = mock_emergency_service.escalate_emergency.call_args[1]
        assert call_kwargs["contact_phone"] == "+1234567890"

    def test_escalate_without_contact_phone(
        self, client: TestClient, user_id: UUID, mock_emergency_service: AsyncMock
    ) -> None:
        """Escalation works without a contact phone."""
        payload = {"user_id": str(user_id), "text": "Emergency situation"}
        response = client.post("/api/v1/emergency/escalate", json=payload)
        assert response.status_code == 200
        call_kwargs = mock_emergency_service.escalate_emergency.call_args[1]
        assert call_kwargs["contact_phone"] is None

    def test_escalate_response_schema(
        self, client: TestClient, valid_escalate_payload: dict[str, Any]
    ) -> None:
        """Response deserializes into EmergencyEscalateResponseSchema."""
        response = client.post("/api/v1/emergency/escalate", json=valid_escalate_payload)
        parsed = EmergencyEscalateResponseSchema.model_validate(response.json())
        assert parsed.escalated is True
        assert parsed.urgency == UrgencyLevel.CRITICAL


# ---------------------------------------------------------------------------
# Test 3: Health Endpoint
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    """Test GET /api/v1/emergency/health endpoint."""

    def test_health_returns_200(self, client: TestClient) -> None:
        """Health check returns 200 when healthy."""
        response = client.get("/api/v1/emergency/health")
        assert response.status_code == 200

    def test_health_returns_status(self, client: TestClient) -> None:
        """Response contains status field."""
        response = client.get("/api/v1/emergency/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_returns_agent_statuses(self, client: TestClient) -> None:
        """Response contains urgency_agent and emergency_agent status."""
        response = client.get("/api/v1/emergency/health")
        data = response.json()
        assert data["urgency_agent"] == "operational"
        assert data["emergency_agent"] == "operational"

    def test_health_failure_returns_503(
        self, client: TestClient, mock_emergency_service: AsyncMock
    ) -> None:
        """Health check failure returns 503."""
        mock_emergency_service.health_check.side_effect = RuntimeError("Agent down")
        response = client.get("/api/v1/emergency/health")
        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"].lower()

    def test_health_response_schema(self, client: TestClient) -> None:
        """Response deserializes into EmergencyHealthResponseSchema."""
        response = client.get("/api/v1/emergency/health")
        parsed = EmergencyHealthResponseSchema.model_validate(response.json())
        assert parsed.status == "healthy"


# ---------------------------------------------------------------------------
# Test 4: Invalid Payload / Error Handling
# ---------------------------------------------------------------------------


class TestInvalidPayload:
    """Test validation errors and error handling."""

    # --- Analyze Validation ---

    def test_analyze_missing_user_id_returns_422(self, client: TestClient) -> None:
        """Missing user_id returns 422."""
        response = client.post(
            "/api/v1/emergency/analyze",
            json={"text": "Emergency"},
        )
        assert response.status_code == 422

    def test_analyze_missing_text_returns_422(self, client: TestClient) -> None:
        """Missing text returns 422."""
        response = client.post(
            "/api/v1/emergency/analyze",
            json={"user_id": str(uuid4())},
        )
        assert response.status_code == 422

    def test_analyze_empty_text_returns_422(self, client: TestClient) -> None:
        """Empty text returns 422."""
        response = client.post(
            "/api/v1/emergency/analyze",
            json={"user_id": str(uuid4()), "text": ""},
        )
        assert response.status_code == 422

    def test_analyze_text_exceeds_max_length_returns_422(self, client: TestClient) -> None:
        """Text exceeding 5000 chars returns 422."""
        response = client.post(
            "/api/v1/emergency/analyze",
            json={"user_id": str(uuid4()), "text": "x" * 5001},
        )
        assert response.status_code == 422

    def test_analyze_invalid_user_id_returns_422(self, client: TestClient) -> None:
        """Non-UUID user_id returns 422."""
        response = client.post(
            "/api/v1/emergency/analyze",
            json={"user_id": "not-a-uuid", "text": "Help"},
        )
        assert response.status_code == 422

    def test_analyze_extra_fields_rejected(self, client: TestClient) -> None:
        """Extra fields are rejected."""
        response = client.post(
            "/api/v1/emergency/analyze",
            json={"user_id": str(uuid4()), "text": "Help", "extra": "nope"},
        )
        assert response.status_code == 422

    # --- Escalate Validation ---

    def test_escalate_missing_text_returns_422(self, client: TestClient) -> None:
        """Missing text on escalate returns 422."""
        response = client.post(
            "/api/v1/emergency/escalate",
            json={"user_id": str(uuid4())},
        )
        assert response.status_code == 422

    def test_escalate_empty_text_returns_422(self, client: TestClient) -> None:
        """Empty text on escalate returns 422."""
        response = client.post(
            "/api/v1/emergency/escalate",
            json={"user_id": str(uuid4()), "text": ""},
        )
        assert response.status_code == 422

    # --- Service Error Handling ---

    def test_analyze_value_error_returns_400(
        self, client: TestClient, valid_analyze_payload: dict[str, Any], mock_emergency_service: AsyncMock
    ) -> None:
        """ValueError from service returns 400."""
        mock_emergency_service.analyze_urgency.side_effect = ValueError("Invalid input")
        response = client.post("/api/v1/emergency/analyze", json=valid_analyze_payload)
        assert response.status_code == 400
        assert "Invalid input" in response.json()["detail"]

    def test_analyze_agent_error_returns_422(
        self, client: TestClient, valid_analyze_payload: dict[str, Any], mock_emergency_service: AsyncMock
    ) -> None:
        """UrgencyAgentException returns 422."""
        mock_emergency_service.analyze_urgency.side_effect = UrgencyAgentException("Agent failed")
        response = client.post("/api/v1/emergency/analyze", json=valid_analyze_payload)
        assert response.status_code == 422
        assert "Agent failed" in response.json()["detail"]

    def test_analyze_internal_error_returns_500(
        self, client: TestClient, valid_analyze_payload: dict[str, Any], mock_emergency_service: AsyncMock
    ) -> None:
        """Unexpected exception returns 500."""
        mock_emergency_service.analyze_urgency.side_effect = RuntimeError("Crash")
        response = client.post("/api/v1/emergency/analyze", json=valid_analyze_payload)
        assert response.status_code == 500
        assert "Failed to analyze" in response.json()["detail"]

    def test_escalate_value_error_returns_400(
        self, client: TestClient, valid_escalate_payload: dict[str, Any], mock_emergency_service: AsyncMock
    ) -> None:
        """ValueError on escalate returns 400."""
        mock_emergency_service.escalate_emergency.side_effect = ValueError("Bad data")
        response = client.post("/api/v1/emergency/escalate", json=valid_escalate_payload)
        assert response.status_code == 400

    def test_escalate_agent_error_returns_422(
        self, client: TestClient, valid_escalate_payload: dict[str, Any], mock_emergency_service: AsyncMock
    ) -> None:
        """UrgencyAgentException on escalate returns 422."""
        mock_emergency_service.escalate_emergency.side_effect = UrgencyAgentException("Oops")
        response = client.post("/api/v1/emergency/escalate", json=valid_escalate_payload)
        assert response.status_code == 422

    def test_escalate_internal_error_returns_500(
        self, client: TestClient, valid_escalate_payload: dict[str, Any], mock_emergency_service: AsyncMock
    ) -> None:
        """Unexpected exception on escalate returns 500."""
        mock_emergency_service.escalate_emergency.side_effect = RuntimeError("Down")
        response = client.post("/api/v1/emergency/escalate", json=valid_escalate_payload)
        assert response.status_code == 500
        assert "Failed to escalate" in response.json()["detail"]
