/**
 * API configuration constants.
 *
 * NEXT_PUBLIC_API_URL must be the bare backend domain (no trailing slash, no /api/v1).
 * Example:
 *   Local:      http://localhost:8000
 *   Production: https://neednow-ai-production.up.railway.app
 *
 * All ENDPOINTS paths include the /api/v1 prefix so requests resolve correctly
 * when Axios appends them to the baseURL.
 */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const API_TIMEOUT = 30_000;

export const ENDPOINTS = {
  CHAT: "/api/v1/chat",
  CHAT_HISTORY: (sessionId: string) => `/api/v1/chat/${sessionId}/history`,
  INTENT: "/api/v1/intent",
  CART: {
    ADD: "/api/v1/cart/add",
    REMOVE: "/api/v1/cart/remove",
    GET: (userId: string) => `/api/v1/cart/${userId}`,
    CLEAR: (userId: string) => `/api/v1/cart/${userId}`,
  },
  MEMORY: {
    STORE: "/api/v1/memory/store",
    GET: (userId: string) => `/api/v1/memory/${userId}`,
    CLEAR: (userId: string) => `/api/v1/memory/${userId}`,
  },
  VOICE: {
    TRANSCRIBE: "/api/v1/voice/transcribe",
    CHAT: "/api/v1/voice/chat",
  },
  EMERGENCY: {
    ANALYZE: "/api/v1/emergency/analyze",
    ESCALATE: "/api/v1/emergency/escalate",
    HEALTH: "/api/v1/emergency/health",
  },
  SUSTAINABILITY: {
    ANALYZE: "/api/v1/sustainability/analyze",
    RECOMMEND: "/api/v1/sustainability/recommend",
    SCORE: (productId: string) => `/api/v1/sustainability/score/${productId}`,
  },
  ORDERS: {
    PLACE: "/api/v1/orders",
    LIST: (userId: string) => `/api/v1/orders/${userId}`,
    GET: (userId: string, orderId: string) => `/api/v1/orders/${userId}/${orderId}`,
  },
} as const;
