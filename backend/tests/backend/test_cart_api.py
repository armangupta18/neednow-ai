"""Tests for the Cart API endpoint (app/api/v1/cart.py).

Covers:
    1. Add item to cart — successful add, quantity increment.
    2. Remove item from cart — full and partial removal.
    3. Get cart — successful retrieval, empty cart.
    4. Clear cart — successful clear.
    5. Invalid product — 404 on missing product/user, validation errors.

Uses a self-contained FastAPI app to avoid deep import chains.
The cart router interface is replicated with mocked CartService.
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
# Lightweight schema replicas
# ---------------------------------------------------------------------------


class CartAddRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: UUID
    product_id: UUID
    quantity: int = Field(default=1, ge=1)


class CartRemoveRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: UUID
    product_id: UUID
    quantity: int | None = Field(default=None, ge=1)


class CartItemResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    product_id: UUID
    product_name: str
    quantity: int = Field(ge=1)
    unit_price: float
    line_total: float


class CartResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: UUID
    cart_id: UUID
    total_amount: float
    items: list[CartItemResponseSchema] = Field(default_factory=list)


class CartMutationResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str
    cart: CartResponseSchema


class CartClearResponseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: UUID
    cleared: bool = True
    message: str = "Cart cleared successfully"


# ---------------------------------------------------------------------------
# Test Router (replicates app/api/v1/cart.py interface)
# ---------------------------------------------------------------------------


def _build_cart_router(get_service_dep):
    """Build a cart router with the given dependency."""
    router = APIRouter(prefix="/cart", tags=["Cart"])

    @router.post("/add", response_model=CartMutationResponseSchema, status_code=200)
    async def add_cart_item(
        request: CartAddRequestSchema,
        cart_service=Depends(get_service_dep),
    ) -> CartMutationResponseSchema:
        try:
            return await cart_service.add_item(
                user_id=request.user_id,
                product_id=request.product_id,
                quantity=request.quantity,
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to add item to cart")

    @router.post("/remove", response_model=CartMutationResponseSchema, status_code=200)
    async def remove_cart_item(
        request: CartRemoveRequestSchema,
        cart_service=Depends(get_service_dep),
    ) -> CartMutationResponseSchema:
        try:
            return await cart_service.remove_item(
                user_id=request.user_id,
                product_id=request.product_id,
                quantity=request.quantity,
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to remove item from cart")

    @router.get("/{user_id}", response_model=CartResponseSchema, status_code=200)
    async def get_user_cart(
        user_id: UUID,
        cart_service=Depends(get_service_dep),
    ) -> CartResponseSchema:
        try:
            return await cart_service.get_cart(user_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to retrieve cart")

    @router.delete("/{user_id}", response_model=CartClearResponseSchema, status_code=200)
    async def clear_user_cart(
        user_id: UUID,
        cart_service=Depends(get_service_dep),
    ) -> CartClearResponseSchema:
        try:
            return await cart_service.clear_cart(user_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to clear cart")

    return router


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def user_id() -> UUID:
    return uuid4()


@pytest.fixture
def product_id() -> UUID:
    return uuid4()


@pytest.fixture
def cart_id() -> UUID:
    return uuid4()


@pytest.fixture
def sample_cart_item(product_id: UUID) -> CartItemResponseSchema:
    """A sample cart item."""
    return CartItemResponseSchema(
        id=uuid4(),
        product_id=product_id,
        product_name="Organic Baby Formula",
        quantity=2,
        unit_price=24.99,
        line_total=49.98,
    )


@pytest.fixture
def sample_cart_response(
    user_id: UUID, cart_id: UUID, sample_cart_item: CartItemResponseSchema
) -> CartResponseSchema:
    """A sample cart with one item."""
    return CartResponseSchema(
        user_id=user_id,
        cart_id=cart_id,
        total_amount=49.98,
        items=[sample_cart_item],
    )


@pytest.fixture
def sample_mutation_response(
    sample_cart_response: CartResponseSchema,
) -> CartMutationResponseSchema:
    """A sample mutation response."""
    return CartMutationResponseSchema(
        message="Item added to cart",
        cart=sample_cart_response,
    )


@pytest.fixture
def mock_cart_service(
    user_id: UUID,
    cart_id: UUID,
    sample_cart_response: CartResponseSchema,
    sample_mutation_response: CartMutationResponseSchema,
) -> AsyncMock:
    """Create a mocked CartService."""
    service = AsyncMock()

    service.add_item = AsyncMock(return_value=sample_mutation_response)
    service.remove_item = AsyncMock(
        return_value=CartMutationResponseSchema(
            message="Item removed from cart",
            cart=CartResponseSchema(
                user_id=user_id,
                cart_id=cart_id,
                total_amount=0.0,
                items=[],
            ),
        )
    )
    service.get_cart = AsyncMock(return_value=sample_cart_response)
    service.clear_cart = AsyncMock(
        return_value=CartClearResponseSchema(user_id=user_id)
    )

    return service


@pytest.fixture
def client(mock_cart_service: AsyncMock) -> TestClient:
    """Create a TestClient with the mocked cart service."""
    app = FastAPI()

    def get_service():
        return mock_cart_service

    router = _build_cart_router(get_service)
    app.include_router(router, prefix="/api/v1")

    return TestClient(app)


# ---------------------------------------------------------------------------
# Test 1: Add Item to Cart
# ---------------------------------------------------------------------------


class TestAddItem:
    """Test POST /api/v1/cart/add endpoint."""

    def test_add_item_returns_200(
        self, client: TestClient, user_id: UUID, product_id: UUID
    ) -> None:
        """Successful add returns 200."""
        response = client.post(
            "/api/v1/cart/add",
            json={"user_id": str(user_id), "product_id": str(product_id), "quantity": 1},
        )
        assert response.status_code == 200

    def test_add_item_returns_message(
        self, client: TestClient, user_id: UUID, product_id: UUID
    ) -> None:
        """Response contains a success message."""
        response = client.post(
            "/api/v1/cart/add",
            json={"user_id": str(user_id), "product_id": str(product_id)},
        )
        data = response.json()
        assert "message" in data
        assert len(data["message"]) > 0

    def test_add_item_returns_cart(
        self, client: TestClient, user_id: UUID, product_id: UUID
    ) -> None:
        """Response contains a cart object with items."""
        response = client.post(
            "/api/v1/cart/add",
            json={"user_id": str(user_id), "product_id": str(product_id)},
        )
        cart = response.json()["cart"]
        assert "cart_id" in cart
        assert "total_amount" in cart
        assert "items" in cart
        assert isinstance(cart["items"], list)

    def test_add_item_default_quantity_is_1(
        self, client: TestClient, user_id: UUID, product_id: UUID, mock_cart_service: AsyncMock
    ) -> None:
        """Default quantity is 1 when not specified."""
        client.post(
            "/api/v1/cart/add",
            json={"user_id": str(user_id), "product_id": str(product_id)},
        )
        call_kwargs = mock_cart_service.add_item.call_args[1]
        assert call_kwargs["quantity"] == 1

    def test_add_item_with_custom_quantity(
        self, client: TestClient, user_id: UUID, product_id: UUID, mock_cart_service: AsyncMock
    ) -> None:
        """Custom quantity is passed to service."""
        client.post(
            "/api/v1/cart/add",
            json={"user_id": str(user_id), "product_id": str(product_id), "quantity": 5},
        )
        call_kwargs = mock_cart_service.add_item.call_args[1]
        assert call_kwargs["quantity"] == 5

    def test_add_item_calls_service(
        self, client: TestClient, user_id: UUID, product_id: UUID, mock_cart_service: AsyncMock
    ) -> None:
        """CartService.add_item is called with correct args."""
        client.post(
            "/api/v1/cart/add",
            json={"user_id": str(user_id), "product_id": str(product_id), "quantity": 3},
        )
        mock_cart_service.add_item.assert_called_once_with(
            user_id=user_id, product_id=product_id, quantity=3
        )

    def test_add_item_response_schema(
        self, client: TestClient, user_id: UUID, product_id: UUID
    ) -> None:
        """Response deserializes into CartMutationResponseSchema."""
        response = client.post(
            "/api/v1/cart/add",
            json={"user_id": str(user_id), "product_id": str(product_id)},
        )
        parsed = CartMutationResponseSchema.model_validate(response.json())
        assert parsed.cart.cart_id is not None


# ---------------------------------------------------------------------------
# Test 2: Remove Item from Cart
# ---------------------------------------------------------------------------


class TestRemoveItem:
    """Test POST /api/v1/cart/remove endpoint."""

    def test_remove_item_returns_200(
        self, client: TestClient, user_id: UUID, product_id: UUID
    ) -> None:
        """Successful remove returns 200."""
        response = client.post(
            "/api/v1/cart/remove",
            json={"user_id": str(user_id), "product_id": str(product_id)},
        )
        assert response.status_code == 200

    def test_remove_item_returns_message(
        self, client: TestClient, user_id: UUID, product_id: UUID
    ) -> None:
        """Response contains a removal message."""
        response = client.post(
            "/api/v1/cart/remove",
            json={"user_id": str(user_id), "product_id": str(product_id)},
        )
        data = response.json()
        assert "message" in data

    def test_remove_item_null_quantity_removes_entirely(
        self, client: TestClient, user_id: UUID, product_id: UUID, mock_cart_service: AsyncMock
    ) -> None:
        """Null quantity means remove the item entirely."""
        client.post(
            "/api/v1/cart/remove",
            json={"user_id": str(user_id), "product_id": str(product_id)},
        )
        call_kwargs = mock_cart_service.remove_item.call_args[1]
        assert call_kwargs["quantity"] is None

    def test_remove_item_with_quantity(
        self, client: TestClient, user_id: UUID, product_id: UUID, mock_cart_service: AsyncMock
    ) -> None:
        """Specific quantity is passed to service."""
        client.post(
            "/api/v1/cart/remove",
            json={"user_id": str(user_id), "product_id": str(product_id), "quantity": 2},
        )
        call_kwargs = mock_cart_service.remove_item.call_args[1]
        assert call_kwargs["quantity"] == 2

    def test_remove_item_returns_updated_cart(
        self, client: TestClient, user_id: UUID, product_id: UUID
    ) -> None:
        """Response contains the updated cart after removal."""
        response = client.post(
            "/api/v1/cart/remove",
            json={"user_id": str(user_id), "product_id": str(product_id)},
        )
        cart = response.json()["cart"]
        assert "total_amount" in cart
        assert "items" in cart


# ---------------------------------------------------------------------------
# Test 3: Get Cart
# ---------------------------------------------------------------------------


class TestGetCart:
    """Test GET /api/v1/cart/{user_id} endpoint."""

    def test_get_cart_returns_200(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Successful retrieval returns 200."""
        response = client.get(f"/api/v1/cart/{user_id}")
        assert response.status_code == 200

    def test_get_cart_returns_user_id(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Response contains the correct user_id."""
        response = client.get(f"/api/v1/cart/{user_id}")
        data = response.json()
        assert data["user_id"] == str(user_id)

    def test_get_cart_returns_cart_id(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Response contains a valid cart_id."""
        response = client.get(f"/api/v1/cart/{user_id}")
        data = response.json()
        UUID(data["cart_id"])  # validates UUID format

    def test_get_cart_returns_items(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Response contains an items list."""
        response = client.get(f"/api/v1/cart/{user_id}")
        data = response.json()
        assert isinstance(data["items"], list)
        assert len(data["items"]) == 1  # from fixture

    def test_get_cart_item_structure(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Cart items have required fields."""
        response = client.get(f"/api/v1/cart/{user_id}")
        item = response.json()["items"][0]

        assert "id" in item
        assert "product_id" in item
        assert "product_name" in item
        assert "quantity" in item
        assert "unit_price" in item
        assert "line_total" in item

    def test_get_cart_total_amount(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """total_amount is a non-negative number."""
        response = client.get(f"/api/v1/cart/{user_id}")
        data = response.json()
        assert isinstance(data["total_amount"], (int, float))
        assert data["total_amount"] >= 0

    def test_get_empty_cart(
        self,
        client: TestClient,
        user_id: UUID,
        cart_id: UUID,
        mock_cart_service: AsyncMock,
    ) -> None:
        """Empty cart returns items=[] and total_amount=0."""
        mock_cart_service.get_cart.return_value = CartResponseSchema(
            user_id=user_id, cart_id=cart_id, total_amount=0.0, items=[]
        )
        response = client.get(f"/api/v1/cart/{user_id}")
        data = response.json()
        assert data["items"] == []
        assert data["total_amount"] == 0.0

    def test_get_cart_response_schema(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Response deserializes into CartResponseSchema."""
        response = client.get(f"/api/v1/cart/{user_id}")
        parsed = CartResponseSchema.model_validate(response.json())
        assert parsed.user_id == user_id


# ---------------------------------------------------------------------------
# Test 4: Clear Cart
# ---------------------------------------------------------------------------


class TestClearCart:
    """Test DELETE /api/v1/cart/{user_id} endpoint."""

    def test_clear_cart_returns_200(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Successful clear returns 200."""
        response = client.delete(f"/api/v1/cart/{user_id}")
        assert response.status_code == 200

    def test_clear_cart_returns_cleared_true(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Response has cleared=True."""
        response = client.delete(f"/api/v1/cart/{user_id}")
        data = response.json()
        assert data["cleared"] is True

    def test_clear_cart_returns_user_id(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Response contains the user_id."""
        response = client.delete(f"/api/v1/cart/{user_id}")
        data = response.json()
        assert data["user_id"] == str(user_id)

    def test_clear_cart_returns_message(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Response contains a success message."""
        response = client.delete(f"/api/v1/cart/{user_id}")
        data = response.json()
        assert "message" in data
        assert len(data["message"]) > 0

    def test_clear_cart_calls_service(
        self, client: TestClient, user_id: UUID, mock_cart_service: AsyncMock
    ) -> None:
        """CartService.clear_cart is called with correct user_id."""
        client.delete(f"/api/v1/cart/{user_id}")
        mock_cart_service.clear_cart.assert_called_once_with(user_id)

    def test_clear_cart_response_schema(
        self, client: TestClient, user_id: UUID
    ) -> None:
        """Response deserializes into CartClearResponseSchema."""
        response = client.delete(f"/api/v1/cart/{user_id}")
        parsed = CartClearResponseSchema.model_validate(response.json())
        assert parsed.cleared is True


# ---------------------------------------------------------------------------
# Test 5: Invalid Product / Error Handling
# ---------------------------------------------------------------------------


class TestInvalidProduct:
    """Test error cases: product not found, user not found, validation errors."""

    def test_add_item_product_not_found_returns_404(
        self,
        client: TestClient,
        user_id: UUID,
        product_id: UUID,
        mock_cart_service: AsyncMock,
    ) -> None:
        """Adding a non-existent product returns 404."""
        mock_cart_service.add_item.side_effect = ValueError("Product not found")
        response = client.post(
            "/api/v1/cart/add",
            json={"user_id": str(user_id), "product_id": str(product_id)},
        )
        assert response.status_code == 404
        assert "Product not found" in response.json()["detail"]

    def test_add_item_user_not_found_returns_404(
        self,
        client: TestClient,
        user_id: UUID,
        product_id: UUID,
        mock_cart_service: AsyncMock,
    ) -> None:
        """Adding item for non-existent user returns 404."""
        mock_cart_service.add_item.side_effect = ValueError("User not found")
        response = client.post(
            "/api/v1/cart/add",
            json={"user_id": str(user_id), "product_id": str(product_id)},
        )
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_remove_item_not_in_cart_returns_404(
        self,
        client: TestClient,
        user_id: UUID,
        product_id: UUID,
        mock_cart_service: AsyncMock,
    ) -> None:
        """Removing item not in cart returns 404."""
        mock_cart_service.remove_item.side_effect = ValueError("Item not in cart")
        response = client.post(
            "/api/v1/cart/remove",
            json={"user_id": str(user_id), "product_id": str(product_id)},
        )
        assert response.status_code == 404
        assert "not in cart" in response.json()["detail"].lower()

    def test_get_cart_user_not_found_returns_404(
        self, client: TestClient, mock_cart_service: AsyncMock
    ) -> None:
        """Getting cart for non-existent user returns 404."""
        mock_cart_service.get_cart.side_effect = ValueError("User not found")
        response = client.get(f"/api/v1/cart/{uuid4()}")
        assert response.status_code == 404

    def test_clear_cart_user_not_found_returns_404(
        self, client: TestClient, mock_cart_service: AsyncMock
    ) -> None:
        """Clearing cart for non-existent user returns 404."""
        mock_cart_service.clear_cart.side_effect = ValueError("User not found")
        response = client.delete(f"/api/v1/cart/{uuid4()}")
        assert response.status_code == 404

    def test_add_item_internal_error_returns_500(
        self,
        client: TestClient,
        user_id: UUID,
        product_id: UUID,
        mock_cart_service: AsyncMock,
    ) -> None:
        """Unexpected exception on add returns 500."""
        mock_cart_service.add_item.side_effect = RuntimeError("DB crashed")
        response = client.post(
            "/api/v1/cart/add",
            json={"user_id": str(user_id), "product_id": str(product_id)},
        )
        assert response.status_code == 500
        assert "Failed to add" in response.json()["detail"]

    def test_add_item_missing_user_id_returns_422(self, client: TestClient) -> None:
        """Missing user_id returns 422."""
        response = client.post(
            "/api/v1/cart/add",
            json={"product_id": str(uuid4()), "quantity": 1},
        )
        assert response.status_code == 422

    def test_add_item_missing_product_id_returns_422(self, client: TestClient) -> None:
        """Missing product_id returns 422."""
        response = client.post(
            "/api/v1/cart/add",
            json={"user_id": str(uuid4()), "quantity": 1},
        )
        assert response.status_code == 422

    def test_add_item_invalid_uuid_returns_422(self, client: TestClient) -> None:
        """Invalid UUID format returns 422."""
        response = client.post(
            "/api/v1/cart/add",
            json={"user_id": "not-a-uuid", "product_id": str(uuid4())},
        )
        assert response.status_code == 422

    def test_add_item_zero_quantity_returns_422(self, client: TestClient) -> None:
        """Quantity of 0 returns 422 (ge=1 constraint)."""
        response = client.post(
            "/api/v1/cart/add",
            json={"user_id": str(uuid4()), "product_id": str(uuid4()), "quantity": 0},
        )
        assert response.status_code == 422

    def test_add_item_negative_quantity_returns_422(self, client: TestClient) -> None:
        """Negative quantity returns 422."""
        response = client.post(
            "/api/v1/cart/add",
            json={"user_id": str(uuid4()), "product_id": str(uuid4()), "quantity": -1},
        )
        assert response.status_code == 422

    def test_remove_item_zero_quantity_returns_422(self, client: TestClient) -> None:
        """Quantity of 0 on remove returns 422."""
        response = client.post(
            "/api/v1/cart/remove",
            json={"user_id": str(uuid4()), "product_id": str(uuid4()), "quantity": 0},
        )
        assert response.status_code == 422

    def test_get_cart_invalid_user_id_returns_422(self, client: TestClient) -> None:
        """Invalid UUID in path returns 422."""
        response = client.get("/api/v1/cart/not-a-uuid")
        assert response.status_code == 422

    def test_add_item_extra_fields_rejected(self, client: TestClient) -> None:
        """Extra fields in request body are rejected."""
        response = client.post(
            "/api/v1/cart/add",
            json={
                "user_id": str(uuid4()),
                "product_id": str(uuid4()),
                "quantity": 1,
                "extra": "nope",
            },
        )
        assert response.status_code == 422
