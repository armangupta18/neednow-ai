/**
 * Order types — maps to backend order API endpoints.
 */

// ---------------------------------------------------------------------------
// Order Item
// ---------------------------------------------------------------------------

export interface OrderItemInput {
  product_id: string;
  product_name: string;
  quantity: number;
  unit_price: number;
}

// ---------------------------------------------------------------------------
// Order Address
// ---------------------------------------------------------------------------

export interface OrderAddress {
  name: string;
  phone: string;
  address: string;
  landmark: string;
  city: string;
  state: string;
  pincode: string;
}

// ---------------------------------------------------------------------------
// Requests
// ---------------------------------------------------------------------------

export interface PlaceOrderRequest {
  user_id: string;
  cart_items: OrderItemInput[];
  address: OrderAddress;
  payment_method: PaymentMethod;
  total_amount: number;
}

// ---------------------------------------------------------------------------
// Responses
// ---------------------------------------------------------------------------

export interface OrderResponse {
  order_id: string;
  status: string;
  estimated_delivery: string;
  total_amount: number;
  payment_method: string;
  address: OrderAddress;
  items: OrderItemInput[];
  created_at: string;
}

export interface OrderListResponse {
  orders: OrderResponse[];
}

// ---------------------------------------------------------------------------
// Payment Methods
// ---------------------------------------------------------------------------

export type PaymentMethod =
  | "cod"
  | "upi"
  | "credit_card"
  | "debit_card"
  | "net_banking";

export const PAYMENT_METHODS: { value: PaymentMethod; label: string; icon: string }[] = [
  { value: "cod", label: "Cash on Delivery", icon: "💵" },
  { value: "upi", label: "UPI", icon: "📱" },
  { value: "credit_card", label: "Credit Card", icon: "💳" },
  { value: "debit_card", label: "Debit Card", icon: "💳" },
  { value: "net_banking", label: "Net Banking", icon: "🏦" },
];
