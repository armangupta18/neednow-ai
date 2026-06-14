export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
export const API_TIMEOUT = 30000;

export const ENDPOINTS = {
  CHAT: "/chat",
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
