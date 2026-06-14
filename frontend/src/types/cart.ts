/**
 * Cart types — maps to backend cart API endpoints.
 */

// ---------------------------------------------------------------------------
// Cart Item (from GET /api/v1/cart/{user_id})
// ---------------------------------------------------------------------------

export interface CartItem {
  id: string;
  product_id: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  line_total: number;
}

// ---------------------------------------------------------------------------
// Cart Response
// ---------------------------------------------------------------------------

export interface CartResponse {
  user_id: string;
  cart_id: string;
  total_amount: number;
  items: CartItem[];
}

// ---------------------------------------------------------------------------
// Cart Mutation
// ---------------------------------------------------------------------------

export interface CartAddRequest {
  user_id: string;
  product_id: string;
  quantity: number;
}

export interface CartRemoveRequest {
  user_id: string;
  product_id: string;
  quantity?: number | null;
}

export interface CartMutationResponse {
  message: string;
  cart: CartResponse;
}

export interface CartClearResponse {
  user_id: string;
  cleared: boolean;
  message: string;
}

// ---------------------------------------------------------------------------
// Cart Helpers
// ---------------------------------------------------------------------------

/** Calculate cart totals client-side */
export function calculateCartTotal(items: CartItem[]): number {
  return items.reduce((sum, item) => sum + item.line_total, 0);
}

/** Count total items in cart */
export function calculateCartItemCount(items: CartItem[]): number {
  return items.reduce((sum, item) => sum + item.quantity, 0);
}

/** Check if a product is in the cart */
export function isInCart(items: CartItem[], productId: string): boolean {
  return items.some((item) => item.product_id === productId);
}

/** Get cart item by product ID */
export function getCartItem(items: CartItem[], productId: string): CartItem | undefined {
  return items.find((item) => item.product_id === productId);
}
