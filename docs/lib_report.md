# Library Modules Report — NeedNow AI Frontend

## Summary

6 library modules implemented in `src/lib/` and `lib/`. All TypeScript, production-ready, zero compilation errors.

---

## Files

| File | Purpose | Key Exports |
|------|---------|-------------|
| `src/lib/api.ts` | Axios HTTP client | `api`, `apiGet`, `apiPost`, `apiDelete`, `ApiError`, `createAbortController` |
| `src/lib/auth.ts` | JWT auth management | `getToken`, `setToken`, `isAuthenticated`, `decodeToken`, `getUserId`, `logout` |
| `src/lib/websocket.ts` | Real-time WS client | `WSClient`, `createChatWS`, `ConnectionState`, `WSMessage` |
| `src/lib/bedrock.ts` | LLM stream consumer | `consumeBedrockStream`, `StreamEvent`, `BEDROCK_MODELS` |
| `src/lib/faiss.ts` | Vector search client | `searchProducts`, `getVectorStats`, `distanceToSimilarity`, `formatSimilarity` |
| `lib/utils.ts` | Shared utilities | `cn`, `formatPrice`, `formatRelativeTime`, `truncate`, `capitalize`, `debounce`, `generateId` |

---

## Module Details

### `api.ts` — HTTP Client
- Axios instance with 30s timeout
- **Request interceptor**: injects `Authorization: Bearer <token>` from auth module
- **Response interceptor**: normalizes all errors into `ApiError` class with `status` + `data`
- Handles 401 by clearing localStorage token
- Typed helpers: `apiGet<T>`, `apiPost<T>`, `apiDelete<T>`
- `createAbortController()` for request cancellation

### `auth.ts` — Authentication
- `getToken()` / `setToken()` / `clearToken()` — localStorage management
- `decodeToken()` — JWT payload decode (client-side, no verification)
- `isAuthenticated()` — checks token existence + expiry
- `isTokenExpired()` / `tokenExpiresIn()` — expiry utilities
- `getUser()` / `setUser()` — stored user profile
- `getUserId()` — extracts from token `sub` claim
- `logout()` — clears all state + redirects
- SSR-safe (checks `typeof window`)

### `websocket.ts` — Real-time Client
- `WSClient` class with lifecycle management
- Auto-reconnect with exponential backoff (1s → 2s → 4s, max 30s)
- Configurable max retries (default: 5)
- Heartbeat/ping every 30s to keep connection alive
- Typed `WSMessage<T>` protocol
- `ConnectionState` tracking: connecting → connected → disconnected → reconnecting
- `createChatWS(sessionId)` — factory for chat streaming

### `bedrock.ts` — LLM Streaming
- `consumeBedrockStream()` — SSE stream reader for Bedrock responses
- Parses `data: {...}\n\n` SSE format
- Typed `StreamEvent` with types: text, thinking, product, cart_update, eco_alert, done, error
- Supports `AbortSignal` for cancellation
- Handles `[DONE]` sentinel
- Constants: `BEDROCK_MODELS`, `BEDROCK_MAX_TOKENS`

### `faiss.ts` — Vector Search
- `searchProducts()` — semantic product search via backend
- `getVectorStats()` — collection statistics
- `distanceToSimilarity()` — cosine distance → percentage
- `formatSimilarity()` — human-readable match quality label
- `similarityColor()` — Tailwind color class by score

### `utils.ts` — Shared Utilities
- `cn()` — Tailwind class merger (clsx + twMerge)
- `formatPrice()` — INR currency formatting
- `formatRelativeTime()` — "2h ago", "yesterday"
- `truncate()` — text with ellipsis
- `capitalize()` — first letter uppercase
- `generateId()` — timestamp + random
- `debounce()` — typed debounce
- `sleep()` — async delay
- `isClient()` — SSR check
- `safeParse()` — JSON.parse without throw

---

## TypeScript Verification

```
$ npx tsc --noEmit
Exit code: 0 — zero errors
```
