"""Order API — endpoints for placing and retrieving orders."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.logger import logger
from app.schemas.order import (
    OrderCreateRequest,
    OrderListResponse,
    OrderResponse,
)
from app.services.order_service import OrderService

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)

# Singleton service instance (in-memory demo mode)
_order_service = OrderService()


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Place a new order",
)
async def place_order(request: OrderCreateRequest) -> OrderResponse:
    """Place a new order from cart items."""
    try:
        response = await _order_service.place_order(request)
        logger.info(
            "Order placed | order_id=%s | user=%s",
            response.order_id,
            str(request.user_id),
        )
        return response
    except Exception:
        logger.exception("Failed to place order")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to place order",
        )


@router.get(
    "/{user_id}",
    response_model=OrderListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all orders for a user",
)
async def get_user_orders(user_id: UUID) -> OrderListResponse:
    """Retrieve all orders for a given user."""
    try:
        response = await _order_service.get_orders(user_id)
        logger.info(
            "Orders retrieved | user=%s | count=%d",
            user_id,
            len(response.orders),
        )
        return response
    except Exception:
        logger.exception("Failed to retrieve orders for user=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve orders",
        )


@router.get(
    "/{user_id}/{order_id}",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a single order",
)
async def get_order(user_id: UUID, order_id: str) -> OrderResponse:
    """Retrieve a single order by ID."""
    try:
        response = await _order_service.get_order(user_id, order_id)
        if response is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found",
            )
        return response
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to retrieve order=%s", order_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve order",
        )
