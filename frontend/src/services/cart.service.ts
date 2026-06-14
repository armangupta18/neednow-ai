/**
 * Cart Service — connects to cart API endpoints.
 */

import { apiPost, apiGet, apiDelete } from "@/lib/api";
import { API_ROUTES } from "@/constants/routes";
import type {
  CartResponse,
  CartMutationResponse,
  CartClearResponse,
  CartAddRequest,
  CartRemoveRequest,
} from "@/types/cart";

// ---------------------------------------------------------------------------
// Cart CRUD
// ---------------------------------------------------------------------------

/** Get the current cart for a user */
export async function getCart(userId: string): Promise<CartResponse> {
  return apiGet<CartResponse>(API_ROUTES.CART.GET(userId));
}

/** Add a product to the cart */
export async function addToCart(
  userId: string,
  productId: string,
  quantity = 1
): Promise<CartMutationResponse> {
  const request: CartAddRequest = {
    user_id: userId,
    product_id: productId,
    quantity,
  };
  return apiPost<CartMutationResponse>(API_ROUTES.CART.ADD, request);
}

/** Remove a product from the cart */
export async function removeFromCart(
  userId: string,
  productId: string,
  quantity?: number
): Promise<CartMutationResponse> {
  const request: CartRemoveRequest = {
    user_id: userId,
    product_id: productId,
    quantity: quantity ?? null,
  };
  return apiPost<CartMutationResponse>(API_ROUTES.CART.REMOVE, request);
}

/** Clear all items from a user's cart */
export async function clearCart(userId: string): Promise<CartClearResponse> {
  return apiDelete<CartClearResponse>(API_ROUTES.CART.CLEAR(userId));
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Add multiple products to cart sequentially */
export async function addMultipleToCart(
  userId: string,
  items: Array<{ productId: string; quantity: number }>
): Promise<CartMutationResponse[]> {
  const results: CartMutationResponse[] = [];
  for (const item of items) {
    const result = await addToCart(userId, item.productId, item.quantity);
    results.push(result);
  }
  return results;
}
