/**
 * Application routes — single source of truth for all navigation paths.
 */

export const ROUTES = {
  // Core pages
  HOME: "/",
  CHAT: "/chat",
  CART: "/cart",
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

/** API endpoint paths (relative to base URL) */
export const API_ROUTES = {
  CHAT: "/chat",
  CHAT_HISTORY: (sessionId: string) => `/chat/${sessionId}/history`,
  INTENT: "/intent",
  CART: {
    ADD: "/cart/add",
    REMOVE: "/cart/remove",
    GET: (userId: string) => `/cart/${userId}`,
    CLEAR: (userId: string) => `/cart/${userId}`,
  },
  MEMORY: {
    STORE: "/memory/store",
    GET: (userId: string) => `/memory/${userId}`,
    CLEAR: (userId: string) => `/memory/${userId}`,
  },
  VOICE: {
    TRANSCRIBE: "/voice/transcribe",
    CHAT: "/voice/chat",
  },
  EMERGENCY: {
    ANALYZE: "/emergency/analyze",
    ESCALATE: "/emergency/escalate",
    HEALTH: "/emergency/health",
  },
  SUSTAINABILITY: {
    ANALYZE: "/sustainability/analyze",
    RECOMMEND: "/sustainability/recommend",
    SCORE: (productId: string) => `/sustainability/score/${productId}`,
  },
} as const;
