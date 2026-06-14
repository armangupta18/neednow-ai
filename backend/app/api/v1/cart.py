from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logger import logger
from app.dependencies.cart import get_cart_service
from app.schemas.cart import (
    CartAddRequest,
    CartClearResponse,
    CartMutationResponse,
    CartRemoveRequest,
    CartResponse,
)
from app.services.cart_service import (
    CartService,
    CartNotFoundError,
    CartServiceError,
    ProductNotFoundError,
)

router = APIRouter(
    prefix="/cart",
    tags=["Cart"],
)


@router.post(
    "/add",
    response_model=CartMutationResponse,
    status_code=status.HTTP_200_OK,
    summary="Add item to cart",
)
async def add_cart_item(
    request: CartAddRequest,
    cart_service: CartService = Depends(get_cart_service),
) -> CartMutationResponse:
    try:
        response = await cart_service.add_item(
            user_id=request.user_id,
            product_id=request.product_id,
            quantity=request.quantity,
        )

        logger.info(
            "Cart item added",
            extra={
                "user_id": str(request.user_id),
                "product_id": str(request.product_id),
                "quantity": request.quantity,
            },
        )

        return response

    except ProductNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except CartServiceError as exc:
        logger.warning("Cart add error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception:
        logger.exception("Failed to add cart item")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add item to cart",
        )


@router.post(
    "/remove",
    response_model=CartMutationResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove item from cart",
)
async def remove_cart_item(
    request: CartRemoveRequest,
    cart_service: CartService = Depends(get_cart_service),
) -> CartMutationResponse:
    try:
        response = await cart_service.remove_item(
            user_id=request.user_id,
            product_id=request.product_id,
            quantity=request.quantity,
        )

        logger.info(
            "Cart item removed",
            extra={
                "user_id": str(request.user_id),
                "product_id": str(request.product_id),
            },
        )

        return response

    except (CartNotFoundError, ProductNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except CartServiceError as exc:
        logger.warning("Cart remove error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception:
        logger.exception("Failed to remove cart item")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove item from cart",
        )


@router.get(
    "/{user_id}",
    response_model=CartResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user cart",
)
async def get_user_cart(
    user_id: UUID,
    cart_service: CartService = Depends(get_cart_service),
) -> CartResponse:
    try:
        response = await cart_service.get_cart(user_id)

        logger.info(
            "Cart retrieved | user=%s | items=%d",
            user_id, len(response.items),
        )

        return response

    except Exception:
        logger.exception("Failed to retrieve cart for user=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cart",
        )


@router.delete(
    "/{user_id}",
    response_model=CartClearResponse,
    status_code=status.HTTP_200_OK,
    summary="Clear user cart",
)
async def clear_user_cart(
    user_id: UUID,
    cart_service: CartService = Depends(get_cart_service),
) -> CartClearResponse:
    try:
        response = await cart_service.clear_cart(user_id)

        logger.info("Cart cleared | user=%s", user_id)

        return response

    except Exception:
        logger.exception("Failed to clear cart for user=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cart",
        )
