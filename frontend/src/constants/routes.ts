/**
 * Application routes — single source of truth for all navigation paths.
 */

export const ROUTES = {
  // Core pages
  HOME: "/",
  CHAT: "/chat",
  CART: "/cart",
  CHECKOUT: "/checkout",
  ORDER_SUCCESS: "/order-success",
  ORDERS: "/orders",
  HISTORY: "/history",

  // Features
  EMERGENCY: "/emergency",
  RECOMMENDATIONS: "/recommendations",
  SUSTAINABILITY: "/sustainability",
  MEMORY: "/memory",
  PROFILE: "/profile",
} as const;

/** Navigation items for header/sidebar */
export const NAV_ITEMS = [
  { label: "Home", href: ROUTES.HOME, icon: "🏠" },
  { label: "Chat", href: ROUTES.CHAT, icon: "💬" },
  { label: "Cart", href: ROUTES.CART, icon: "🛒" },
  { label: "Sustainability", href: ROUTES.SUSTAINABILITY, icon: "🌱" },
  { label: "History", href: ROUTES.HISTORY, icon: "📋" },
] as const;

/** API endpoint paths — all include /api/v1 prefix */
export const API_ROUTES = {
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
