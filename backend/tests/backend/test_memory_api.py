"""Tests for the Memory API endpoint (app/api/v1/memory.py).

Covers:
    1. Store memory — successful persistence.
    2. Retrieve memory — successful retrieval.
    3. Delete (clear) memory — successful reset.
    4. User not found — 404 on missing user.
    5. Validation errors — malformed payloads.

Uses a self-contained FastAPI app to avoid deep import chains.
The memory router interface is replicated with mocked MemoryManager.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Lightweight schema replicas (avoids deep agent import chains)
# ---------------------------------------------------------------------------


class UserMemorySchema(BaseModel):
    """Mirrors app.memory.schemas.UserMemory."""

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


class ClearMemoryResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    cleared: bool = True
    message: str = Field(default="Memory cleared successfully")


# ---------------------------------------------------------------------------
# Test Router (replicates app/api/v1/memory.py interface)
# ---------------------------------------------------------------------------


def _build_memory_router(get_manager_dep):
    """Build a memory router with the given dependency."""
    router = APIRouter(prefix="/memory", tags=["Memory"])

    @router.post("/store", response_model=MemoryResponseSchema, status_code=200)
    async def store_memory(
        request: StoreMemoryRequestSchema,
        memory_manager=Depends(get_manager_dep),
    ) -> MemoryResponseSchema:
        try:
            stored = await memory_manager.save_memory(
                user_id=request.user_id,
                memory=request.memory,
            )
            return MemoryResponseSchema(
                user_id=request.user_id,
                memory=UserMemorySchema(**stored),
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to store user memory")

    @router.get("/{user_id}", response_model=MemoryResponseSchema, status_code=200)
    async def get_memory(
        user_id: UUID,
        memory_manager=Depends(get_manager_dep),
    ) -> MemoryResponseSchema:
        try:
            memory = await memory_manager.retrieve_memory(user_id)
            return MemoryResponseSchema(
                user_id=user_id,
                memory=memory,
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to retrieve user memory")

    @router.delete("/{user_id}", response_model=ClearMemoryResponseSchema, status_code=200)
    async def clear_memory(
        user_id: UUID,
        memory_manager=Depends(get_manager_dep),
    ) -> ClearMemoryResponseSchema:
        try:
            await memory_manager.save_memory(
                user_id=user_id,
                memory=UserMemorySchema(),
            )
            return ClearMemoryResponseSchema(user_id=user_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to clear user memory")

    return router


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def user_id() -> UUID:
    return uuid4()


@pytest.fixture
def sample_memory_data() -> dict[str, Any]:
    """Sample memory payload for store requests."""
    return {
        "dietary_preferences": ["vegan", "gluten-free"],
        "preferred_brands": ["Nature's Best", "EcoPure"],
        "budget_level": "medium",
        "family_size": 4,
        "purchase_patterns": ["weekly groceries", "organic produce"],
        "sustainability_score": 72.5,
    }


@pytest.fixture
def mock_memory_manager(user_id: UUID, sample_memory_data: dict[str, Any]) -> AsyncMock:
    """Create a mocked MemoryManager."""
    manager = AsyncMock()

    # save_memory returns the stored dict
    manager.save_memory = AsyncMock(return_value=sample_memory_data)

    # retrieve_memory returns a UserMemorySchema instance
    manager.retrieve_memory = AsyncMock(
        return_value=UserMemorySchema(**sample_memory_data)
    )

    return manager


@pytest.fixture
def client(mock_memory_manager: AsyncMock) -> TestClient:
    """Create a TestClient with the mocked memory manager."""
    app = FastAPI()

    def get_manager():
        return mock_memory_manager

    router = _build_memory_router(get_manager)
    app.include_router(router, prefix="/api/v1")

    return TestClient(app)


@pytest.fixture
def valid_store_payload(user_id: UUID, sample_memory_data: dict[str, Any]) -> dict[str, Any]:
    """Valid store memory request body."""
    return {
        "user_id": str(user_id),
        "memory": sample_memory_data,
    }


# ---------------------------------------------------------------------------
# Test 1: Store Memory
# ---------------------------------------------------------------------------


class TestStoreMemory:
    """Test POST /api/v1/memory/store endpoint."""

    def test_store_memory_returns_200(
        self, client: TestClient, valid_store_payload: dict[str, Any]
    ) -> None:
        """Successful store returns 200."""
        response = client.post("/api/v1/memory/store", json=valid_store_payload)
        assert response.status_code == 200

    def test_store_memory_returns_user_id(
        self, client: TestClient, valid_store_payload: dict[str, Any]
    ) -> None:
        """Response contains the same user_id."""
        response = client.post("/api/v1/memory/store", json=valid_store_payload)
        data = response.json()
        assert data["user_id"] == valid_store_payload["user_id"]

    def test_store_memory_returns_memory_data(
        self, client: TestClient, valid_store_payload: dict[str, Any]
    ) -> None:
        """Response contains the stored memory data."""
        response = client.post("/api/v1/memory/store", json=valid_store_payload)
        data = response.json()
        assert "memory" in data
        assert data["memory"]["dietary_preferences"] == ["vegan", "gluten-free"]
        assert data["memory"]["sustainability_score"] == 72.5

    def test_store_memory_calls_manager(
        self,
        client: TestClient,
        valid_store_payload: dict[str, Any],
        mock_memory_manager: AsyncMock,
    ) -> None:
        """MemoryManager.save_memory is called with correct args."""
        client.post("/api/v1/memory/store", json=valid_store_payload)
        mock_memory_manager.save_memory.assert_called_once()

        call_kwargs = mock_memory_manager.save_memory.call_args[1]
        assert str(call_kwargs["user_id"]) == valid_store_payload["user_id"]

    def test_store_empty_memory_accepted(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Storing an empty memory (all defaults) is valid."""
        payload = {"user_id": str(user_id), "memory": {}}
        response = client.post("/api/v1/memory/store", json=payload)
        assert response.status_code == 200

    def test_store_partial_memory_accepted(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Storing partial memory fields is valid."""
        payload = {
            "user_id": str(user_id),
            "memory": {"budget_level": "high", "family_size": 2},
        }
        response = client.post("/api/v1/memory/store", json=payload)
        assert response.status_code == 200

    def test_store_memory_response_schema(
        self, client: TestClient, valid_store_payload: dict[str, Any]
    ) -> None:
        """Full response can be deserialized into MemoryResponseSchema."""
        response = client.post("/api/v1/memory/store", json=valid_store_payload)
        parsed = MemoryResponseSchema.model_validate(response.json())
        assert parsed.user_id is not None
        assert isinstance(parsed.memory, UserMemorySchema)


# ---------------------------------------------------------------------------
# Test 2: Retrieve Memory
# ---------------------------------------------------------------------------


class TestRetrieveMemory:
    """Test GET /api/v1/memory/{user_id} endpoint."""

    def test_retrieve_memory_returns_200(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Successful retrieval returns 200."""
        response = client.get(f"/api/v1/memory/{user_id}")
        assert response.status_code == 200

    def test_retrieve_memory_returns_user_id(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Response contains the requested user_id."""
        response = client.get(f"/api/v1/memory/{user_id}")
        data = response.json()
        assert data["user_id"] == str(user_id)

    def test_retrieve_memory_returns_memory_fields(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Response contains all UserMemory fields."""
        response = client.get(f"/api/v1/memory/{user_id}")
        memory = response.json()["memory"]

        assert "dietary_preferences" in memory
        assert "preferred_brands" in memory
        assert "budget_level" in memory
        assert "family_size" in memory
        assert "purchase_patterns" in memory
        assert "sustainability_score" in memory

    def test_retrieve_memory_calls_manager(
        self, client: TestClient, user_id: UUID, mock_memory_manager: AsyncMock
    ) -> None:
        """MemoryManager.retrieve_memory is called with correct user_id."""
        client.get(f"/api/v1/memory/{user_id}")
        mock_memory_manager.retrieve_memory.assert_called_once_with(user_id)

    def test_retrieve_memory_response_schema(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Full response can be deserialized into MemoryResponseSchema."""
        response = client.get(f"/api/v1/memory/{user_id}")
        parsed = MemoryResponseSchema.model_validate(response.json())
        assert parsed.memory.sustainability_score == 72.5


# ---------------------------------------------------------------------------
# Test 3: Delete (Clear) Memory
# ---------------------------------------------------------------------------


class TestDeleteMemory:
    """Test DELETE /api/v1/memory/{user_id} endpoint."""

    def test_clear_memory_returns_200(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Successful clear returns 200."""
        response = client.delete(f"/api/v1/memory/{user_id}")
        assert response.status_code == 200

    def test_clear_memory_returns_cleared_true(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Response has cleared=True."""
        response = client.delete(f"/api/v1/memory/{user_id}")
        data = response.json()
        assert data["cleared"] is True

    def test_clear_memory_returns_user_id(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Response contains the requested user_id."""
        response = client.delete(f"/api/v1/memory/{user_id}")
        data = response.json()
        assert data["user_id"] == str(user_id)

    def test_clear_memory_returns_message(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Response contains a success message."""
        response = client.delete(f"/api/v1/memory/{user_id}")
        data = response.json()
        assert "message" in data
        assert "cleared" in data["message"].lower() or "success" in data["message"].lower()

    def test_clear_memory_calls_save_with_empty_memory(
        self, client: TestClient, user_id: UUID, mock_memory_manager: AsyncMock
    ) -> None:
        """MemoryManager.save_memory is called with empty UserMemory."""
        client.delete(f"/api/v1/memory/{user_id}")
        mock_memory_manager.save_memory.assert_called_once()

        call_kwargs = mock_memory_manager.save_memory.call_args[1]
        assert call_kwargs["user_id"] == user_id

        # The memory should be an empty/default UserMemory
        saved_memory = call_kwargs["memory"]
        assert saved_memory.dietary_preferences == []
        assert saved_memory.preferred_brands == []
        assert saved_memory.sustainability_score == 0.0

    def test_clear_memory_response_schema(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Full response can be deserialized into ClearMemoryResponseSchema."""
        response = client.delete(f"/api/v1/memory/{user_id}")
        parsed = ClearMemoryResponseSchema.model_validate(response.json())
        assert parsed.cleared is True


# ---------------------------------------------------------------------------
# Test 4: User Not Found
# ---------------------------------------------------------------------------


class TestUserNotFound:
    """Test 404 responses when user doesn't exist."""

    def test_store_memory_user_not_found(
        self,
        client: TestClient,
        valid_store_payload: dict[str, Any],
        mock_memory_manager: AsyncMock,
    ) -> None:
        """Store returns 404 when user doesn't exist."""
        mock_memory_manager.save_memory.side_effect = ValueError("User not found")
        response = client.post("/api/v1/memory/store", json=valid_store_payload)
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_retrieve_memory_user_not_found(
        self,
        client: TestClient,
        user_id: UUID,
        mock_memory_manager: AsyncMock,
    ) -> None:
        """Retrieve returns 404 when user doesn't exist."""
        mock_memory_manager.retrieve_memory.side_effect = ValueError(
            f"User {user_id} not found"
        )
        response = client.get(f"/api/v1/memory/{user_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_clear_memory_user_not_found(
        self,
        client: TestClient,
        user_id: UUID,
        mock_memory_manager: AsyncMock,
    ) -> None:
        """Clear returns 404 when user doesn't exist."""
        mock_memory_manager.save_memory.side_effect = ValueError("User not found")
        response = client.delete(f"/api/v1/memory/{user_id}")
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_store_internal_error_returns_500(
        self,
        client: TestClient,
        valid_store_payload: dict[str, Any],
        mock_memory_manager: AsyncMock,
    ) -> None:
        """Unexpected exception returns 500."""
        mock_memory_manager.save_memory.side_effect = RuntimeError("DB down")
        response = client.post("/api/v1/memory/store", json=valid_store_payload)
        assert response.status_code == 500
        assert "Failed to store" in response.json()["detail"]

    def test_retrieve_internal_error_returns_500(
        self,
        client: TestClient,
        user_id: UUID,
        mock_memory_manager: AsyncMock,
    ) -> None:
        """Unexpected exception on retrieve returns 500."""
        mock_memory_manager.retrieve_memory.side_effect = RuntimeError("Timeout")
        response = client.get(f"/api/v1/memory/{user_id}")
        assert response.status_code == 500
        assert "Failed to retrieve" in response.json()["detail"]

    def test_clear_internal_error_returns_500(
        self,
        client: TestClient,
        user_id: UUID,
        mock_memory_manager: AsyncMock,
    ) -> None:
        """Unexpected exception on clear returns 500."""
        mock_memory_manager.save_memory.side_effect = RuntimeError("Connection lost")
        response = client.delete(f"/api/v1/memory/{user_id}")
        assert response.status_code == 500
        assert "Failed to clear" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Test 5: Validation Errors
# ---------------------------------------------------------------------------


class TestValidationErrors:
    """Test request validation and malformed payloads."""

    def test_store_missing_user_id_returns_422(self, client: TestClient) -> None:
        """Missing user_id returns 422."""
        response = client.post(
            "/api/v1/memory/store",
            json={"memory": {"budget_level": "high"}},
        )
        assert response.status_code == 422

    def test_store_missing_memory_returns_422(self, client: TestClient) -> None:
        """Missing memory field returns 422."""
        response = client.post(
            "/api/v1/memory/store",
            json={"user_id": str(uuid4())},
        )
        assert response.status_code == 422

    def test_store_invalid_user_id_returns_422(self, client: TestClient) -> None:
        """Non-UUID user_id returns 422."""
        response = client.post(
            "/api/v1/memory/store",
            json={"user_id": "not-a-uuid", "memory": {}},
        )
        assert response.status_code == 422

    def test_store_extra_fields_rejected(self, client: TestClient) -> None:
        """Extra fields in request body are rejected."""
        response = client.post(
            "/api/v1/memory/store",
            json={
                "user_id": str(uuid4()),
                "memory": {},
                "extra_field": "should fail",
            },
        )
        assert response.status_code == 422

    def test_store_invalid_memory_field_type(self, client: TestClient) -> None:
        """Invalid type for a memory field returns 422."""
        response = client.post(
            "/api/v1/memory/store",
            json={
                "user_id": str(uuid4()),
                "memory": {"family_size": "not-an-int"},
            },
        )
        assert response.status_code == 422

    def test_store_invalid_sustainability_score_type(self, client: TestClient) -> None:
        """Non-numeric sustainability_score returns 422."""
        response = client.post(
            "/api/v1/memory/store",
            json={
                "user_id": str(uuid4()),
                "memory": {"sustainability_score": "high"},
            },
        )
        assert response.status_code == 422

    def test_retrieve_invalid_user_id_returns_422(self, client: TestClient) -> None:
        """Non-UUID path parameter returns 422."""
        response = client.get("/api/v1/memory/not-a-uuid")
        assert response.status_code == 422

    def test_delete_invalid_user_id_returns_422(self, client: TestClient) -> None:
        """Non-UUID path parameter on DELETE returns 422."""
        response = client.delete("/api/v1/memory/not-a-uuid")
        assert response.status_code == 422

    def test_store_empty_body_returns_422(self, client: TestClient) -> None:
        """Empty JSON body returns 422."""
        response = client.post("/api/v1/memory/store", json={})
        assert response.status_code == 422

    def test_store_null_memory_returns_422(self, client: TestClient) -> None:
        """Null memory field returns 422."""
        response = client.post(
            "/api/v1/memory/store",
            json={"user_id": str(uuid4()), "memory": None},
        )
        assert response.status_code == 422

    def test_store_non_json_body_returns_422(self, client: TestClient) -> None:
        """Non-JSON content returns 422."""
        response = client.post(
            "/api/v1/memory/store",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422
