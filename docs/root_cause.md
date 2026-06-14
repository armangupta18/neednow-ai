# Root Cause Analysis — Chat Send Button Issue

## Root Cause

**Network misconfiguration: The frontend sends API requests to `localhost:8000` but the user's browser runs on a different machine (IP `10.55.97.116`) than the backend server (`10.26.29.116`).**

When `.env.local` contains `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`, the browser on the client device interprets `localhost` as itself — not the server hosting the backend. The request never reaches the FastAPI server.

Additionally, the backend CORS policy (`ALLOWED_ORIGINS`) only permitted `http://localhost:3000`, blocking requests from the actual frontend origin (`http://10.26.29.116:3000`).

## Why It Appears as "Button Not Working"

1. User clicks Send → `handleSend()` fires → `onSend(trimmed)` calls `useChat.sendChatMessage`
2. `sendChatMessage` adds optimistic user message (renders in UI) ✅
3. `setIsTyping(true)` → typing indicator shows ✅
4. `apiPost("/chat", request)` fires axios POST to `http://localhost:8000/api/v1/chat`
5. **Request fails immediately** — either:
   - `ERR_CONNECTION_REFUSED` (no server on client's localhost:8000)
   - CORS error (origin mismatch)
6. Error caught → error message added as assistant bubble
7. `setIsTyping(false)` re-enables input
8. **This happens so fast** the user sees: button briefly disabled → nothing meaningful appears (or an error bubble they don't notice at the bottom)

## Fix

1. `.env.local` → `NEXT_PUBLIC_API_URL=http://10.26.29.116:8000/api/v1` (use actual server IP)
2. Backend CORS → allow `"*"` or the specific frontend origin IPs
3. Backend must run with `--host 0.0.0.0` to accept connections from other devices
