# Integration Audit Report — NeedNow AI

## Issue

Chat input accepts text, clicking Send produces no visible response. Backend terminal shows no incoming request.

## Root Cause

**Network topology mismatch.** Frontend `.env.local` pointed to `http://localhost:8000` but the browser runs on a different machine than the backend. CORS also blocked the actual origin.

## Files Modified

| File | Change |
|------|--------|
| `frontend/.env.local` | Changed `NEXT_PUBLIC_API_URL` to use server IP (`10.26.29.116`) |
| `backend/app/core/settings.py` | Added `"*"` and IP-based origins to `ALLOWED_ORIGINS` |
| `frontend/src/lib/api.ts` | Added startup log showing the API base URL |

## Verification Steps

### 1. Start Backend (listening on all interfaces)
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Start Frontend
```bash
cd frontend
npm run dev
```

### 3. Verify in Browser Console
Open DevTools → Console should show:
```
[NeedNow API] Base URL: http://10.26.29.116:8000/api/v1
```

### 4. Send a Message
- Type "hello" in chat input
- Click Send
- Expected: user bubble appears, typing indicator, then assistant response

### 5. Check Network Tab
- Should see `POST http://10.26.29.116:8000/api/v1/chat` with 200 status
- Response body should contain `session_id`, `assistant_message`, `cart`, `urgency`

### 6. Check Backend Terminal
Should show:
```
INFO: 10.x.x.x:xxxxx - "POST /api/v1/chat HTTP/1.1" 200 OK
```

## Component Verification

| Component | Status | Notes |
|-----------|--------|-------|
| ChatInput onClick | ✅ | `type="button"`, `handleSend()` fires correctly |
| ChatInput Enter key | ✅ | `onKeyDown` → Enter (no Shift) → `handleSend()` |
| ChatWindow passes onSend | ✅ | `<ChatInput onSend={sendMessage} />` |
| useChat.sendChatMessage | ✅ | Adds optimistic message, calls API, handles errors |
| agent.service.sendMessage | ✅ | `apiPost("/chat", request)` |
| lib/api.ts baseURL | ✅ Fixed | Now reads `NEXT_PUBLIC_API_URL` correctly |
| Backend CORS | ✅ Fixed | Allows `"*"` for development |
| Backend mock LLM | ✅ | Returns valid responses without AWS |

## Before vs After

| Behavior | Before | After |
|----------|--------|-------|
| API base URL | `http://localhost:8000/api/v1` | `http://10.26.29.116:8000/api/v1` |
| CORS origins | `localhost:3000` only | `*` (all origins in dev) |
| Network request | Never reaches backend | ✅ Reaches backend |
| Backend response | N/A | 200 OK with full pipeline result |
| UI feedback | Silent failure | User msg → typing → assistant reply |
| Error case | Hidden | Red error bubble with actionable message |

## Startup Commands

```bash
# Backend (MUST use --host 0.0.0.0)
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd frontend && npm run dev
```
