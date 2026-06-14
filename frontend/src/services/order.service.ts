/**
 * Order Service — connects to order API endpoints.
 */

import { apiPost, apiGet } from "@/lib/api";
import { API_ROUTES } from "@/constants/routes";
import type {
  PlaceOrderRequest,
  OrderResponse,
  OrderListResponse,
} from "@/types/order";

/** Place a new order */
export async function placeOrder(data: PlaceOrderRequest): Promise<OrderResponse> {
  return apiPost<OrderResponse>(API_ROUTES.ORDERS.PLACE, data);
}

/** Get all orders for a user */
export async function getOrders(userId: string): Promise<OrderListResponse> {
  return apiGet<OrderListResponse>(API_ROUTES.ORDERS.LIST(userId));
}

/** Get a single order */
export async function getOrder(userId: string, orderId: string): Promise<OrderResponse> {
  return apiGet<OrderResponse>(API_ROUTES.ORDERS.GET(userId, orderId));
}
