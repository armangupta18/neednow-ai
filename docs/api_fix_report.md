# API Integration Fix Report — NeedNow AI Frontend

## Issues Found

| # | Severity | File | Issue |
|---|----------|------|-------|
| 1 | **CRITICAL** | `src/hooks/useSupervisor.ts` | Calls non-existent endpoint `/api/v1/supervisor` |
| 2 | **CRITICAL** | `src/hooks/useSupervisor.ts` | Sends `user_id: "demo-user"` (not a valid UUID) |
| 3 | **HIGH** | `src/hooks/useSupervisor.ts` | No error handling, no typed response, no cancellation |
| 4 | **HIGH** | `src/hooks/useSupervisor.ts` | Uses raw `fetch` instead of shared axios instance |
| 5 | **MEDIUM** | `src/hooks/useIntent.ts` | Hardcoded UUID for user_id |
| 6 | **MEDIUM** | `src/services/api.ts` | No timeout, no interceptors, no cancellation support |
| 7 | **LOW** | `src/services/api.ts` | Hardcoded `localhost:8000` (should use env variable) |

---

## Backend API Contract

### `POST /api/v1/chat`

**Request:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "I need baby formula urgently",
  "session_id": null
}
```

**Response (ChatResponse):**
```json
{
  "session_id": "uuid",
  "user_message": { "user_id": "uuid", "session_id": "uuid", "content": "...", "role": "user", "metadata": {}, "timestamp": "..." },
  "assistant_message": { "user_id": "uuid", "session_id": "uuid", "content": "...", "role": "assistant", "metadata": {}, "timestamp": "..." },
  "cart": { "category": "baby", "products": [...], "bundles": [...] },
  "urgency": { "level": "HIGH", "score": 78, "explanation": "..." },
  "reasoning": "...",
  "eco_alternative": { ... } | null,
  "recommended_products": [],
  "metadata": { "memory_used": true, "confidence": 0.93 },
  "timestamp": "2026-06-14T..."
}
```

---

## Fix Plan

### 1. Create `src/services/chatApi.ts` (NEW)

Fully typed API service with loading, errors, cancellation, and timeout.

```typescript
import api from "./api";
import { AxiosError, CancelTokenSource } from "axios";

// --- Types ---

export interface ChatRequest {
  user_id: string;
  message: string;
  session_id?: string | null;
}

export interface AgentMessage {
  user_id: string;
  session_id: string;
  content: string;
  role: "user" | "assistant" | "system";
  metadata: Record<string, unknown>;
  timestamp: string;
}

export interface CartProduct {
  id: string;
  title: string;
  price: number;
  score: number;
}

export interface BundleProduct {
  id: string;
  title: string;
  price: number;
}

export interface SupervisorCart {
  category: string;
  products: CartProduct[];
  bundles: BundleProduct[];
}

export interface Urgency {
  level: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  score: number;
  explanation: string;
}

export interface EcoAlternative {
  original_product_id: string;
  original_product_name: string;
  alternative_product_id: string;
  alternative_product_name: string;
  carbon_saved: number;
  price_difference: number;
  sustainability_score: number;
}

export interface ChatResponse {
  session_id: string;
  user_message: AgentMessage;
  assistant_message: AgentMessage;
  cart: SupervisorCart;
  urgency: Urgency;
  reasoning: string;
  eco_alternative: EcoAlternative | null;
  recommended_products: Record<string, unknown>[];
  metadata: { memory_used: boolean; confidence: number };
  timestamp: string;
}

// --- API Functions ---

export async function sendChatMessage(
  request: ChatRequest,
  cancelToken?: CancelTokenSource
): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>("/chat", request, {
    cancelToken: cancelToken?.token,
    timeout: 30000,
  });
  return response.data;
}
```

### 2. Update `src/services/api.ts`

```typescript
import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

// Response interceptor for error normalization
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error?.response?.data?.detail || error.message || "Request failed";
    return Promise.reject(new Error(message));
  }
);

export default api;
```

### 3. Replace `src/hooks/useSupervisor.ts` → `src/hooks/useChat.ts`

```typescript
"use client";

import { useState, useRef, useCallback } from "react";
import axios, { CancelTokenSource } from "axios";
import { sendChatMessage, ChatResponse } from "@/services/chatApi";

export function useChat() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const cancelRef = useRef<CancelTokenSource | null>(null);

  const sendMessage = useCallback(async (
    message: string,
    userId: string,
    sessionId?: string | null,
  ) => {
    // Cancel previous request
    cancelRef.current?.cancel("New request");
    cancelRef.current = axios.CancelToken.source();

    try {
      setLoading(true);
      setError(null);

      const response = await sendChatMessage(
        { user_id: userId, message, session_id: sessionId },
        cancelRef.current,
      );

      setData(response);
      return response;
    } catch (err: unknown) {
      if (!axios.isCancel(err)) {
        const msg = err instanceof Error ? err.message : "Something went wrong";
        setError(msg);
      }
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const cancel = useCallback(() => {
    cancelRef.current?.cancel("Cancelled by user");
  }, []);

  return { loading, error, data, sendMessage, cancel };
}
```

### 4. Update `src/hooks/useIntent.ts` (minor fixes)

- Remove hardcoded UUID (accept as parameter)
- Add cancellation support

```typescript
"use client";

import { useState, useRef, useCallback } from "react";
import axios, { CancelTokenSource } from "axios";
import api from "@/services/api";

export interface IntentResponse {
  category: string;
  urgency: "low" | "medium" | "high" | "critical";
  budget: number | null;
  people_count: number | null;
  confidence: number;
}

export function useIntent() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<IntentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const cancelRef = useRef<CancelTokenSource | null>(null);

  const analyzeIntent = useCallback(async (text: string, userId: string) => {
    cancelRef.current?.cancel();
    cancelRef.current = axios.CancelToken.source();

    try {
      setLoading(true);
      setError(null);

      const response = await api.post<IntentResponse>("/intent", {
        text,
        user_id: userId,
      }, { cancelToken: cancelRef.current.token, timeout: 15000 });

      setData(response.data);
      return response.data;
    } catch (err: unknown) {
      if (!axios.isCancel(err)) {
        const msg = err instanceof Error ? err.message : "Something went wrong";
        setError(msg);
      }
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { loading, error, data, analyzeIntent };
}
```

---

## Migration Steps

| Step | Action | Files |
|------|--------|-------|
| 1 | Create `.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1` | `.env.local` |
| 2 | Update `src/services/api.ts` with timeout + interceptors | `api.ts` |
| 3 | Create `src/services/chatApi.ts` | NEW |
| 4 | Create `src/hooks/useChat.ts` (replaces `useSupervisor.ts`) | NEW |
| 5 | Update `src/hooks/useIntent.ts` | MODIFIED |
| 6 | Update `src/app/page.tsx` to use `useChat` instead of `useSupervisor` | MODIFIED |
| 7 | Delete `src/hooks/useSupervisor.ts` | DELETE |
| 8 | Update `src/store/useRecommendationStore.ts` type to match `ChatResponse` | MODIFIED |

---

## Breaking Changes

| Component | Current Import | New Import |
|-----------|---------------|------------|
| `src/app/page.tsx` | `useSupervisor` → `generateCart()` | `useChat` → `sendMessage()` |
| `src/store/useRecommendationStore.ts` | `SupervisorResponse` from `@/types/recommendation` | `ChatResponse` from `@/services/chatApi` |
| `src/components/recommendation/ResultSection.tsx` | `result.urgency_level` | `result.urgency.level` |
| `src/components/recommendation/ResultSection.tsx` | `result.products` | `result.cart.products` |

---

## Environment Variables Needed

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```
