import api from "./api";
import { ENDPOINTS } from "@/constants/api";

export interface CartItem {
  id: string;
  product_id: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  line_total: number;
}

export interface CartResponse {
  user_id: string;
  cart_id: string;
  total_amount: number;
  items: CartItem[];
}

export interface CartMutationResponse {
  message: string;
  cart: CartResponse;
}

export async function addToCart(userId: string, productId: string, quantity = 1) {
  const response = await api.post<CartMutationResponse>(ENDPOINTS.CART.ADD, {
    user_id: userId,
    product_id: productId,
    quantity,
  });
  return response.data;
}

export async function removeFromCart(userId: string, productId: string, quantity?: number) {
  const response = await api.post<CartMutationResponse>(ENDPOINTS.CART.REMOVE, {
    user_id: userId,
    product_id: productId,
    quantity: quantity ?? null,
  });
  return response.data;
}

export async function getCart(userId: string) {
  const response = await api.get<CartResponse>(ENDPOINTS.CART.GET(userId));
  return response.data;
}

export async function clearCart(userId: string) {
  const response = await api.delete(ENDPOINTS.CART.CLEAR(userId));
  return response.data;
}
