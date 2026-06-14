# Chat Flow Trace Report — NeedNow AI

## Actual Rendered Component on `/chat`

**`ChatInput.tsx`** is the input component rendered on the `/chat` page.

Path: `app/chat/page.tsx` → `ChatWindow.tsx` → `ChatInput.tsx`

The legacy `SituationInput.tsx` is **NOT** rendered on `/chat`. It was part of the old `/` (home) page architecture and is now unused on the chat route.

---

## Complete Execution Path

```
/chat (page.tsx)
  └── <ChatWindow />
        ├── <ChatInput onSend={sendMessage} />      ← INPUT COMPONENT
        │       │
        │       ├── User types text in <textarea>
        │       ├── User clicks Send button → onClick → handleSend()
        │       ├── OR presses Enter (no Shift) → handleKeyDown → handleSend()
        │       │
        │       └── handleSend() → onSend(trimmed)  ← CALLS PARENT
        │
        └── sendMessage (from useChat hook)
                │
                ├── useChat().sendChatMessage(message)
                │       ├── Adds optimistic user message to store
                │       ├── Sets isTyping = true
                │       │
                │       └── agent.service.sendMessage(request, signal)
                │               │
                │               └── apiPost<ChatResponse>("/chat", request)
                │                       │
                │                       └── axios.post("http://localhost:8000/api/v1/chat", {
                │                               user_id: "550e8400-...",
                │                               message: "...",
                │                               session_id: null
                │                           })
                │
                └── On response:
                        ├── setSessionId
                        ├── addMessage (assistant)
                        ├── setLastResult (cart, urgency, reasoning, eco)
                        └── setIsTyping(false)
```

---

## Verification Results

| Check | Status | Details |
|-------|--------|---------|
| Component rendered | ✅ `ChatInput.tsx` | Not SituationInput |
| Send button onClick | ✅ | `onClick={handleSend}` |
| Enter key handler | ✅ | `onKeyDown` → Enter (no Shift) → `handleSend()` |
| handleSubmit executes | ✅ | Trims value, calls `onSend(trimmed)`, clears input |
| onSend passed from parent | ✅ | `<ChatInput onSend={sendMessage}>` in ChatWindow |
| API request triggered | ✅ | `apiPost("/chat", {...})` via axios |
| Abort support | ✅ | `AbortController` in useChat |
| Error handling | ✅ | Error message shown as assistant bubble |

---

## Root Cause Analysis

**No broken wiring found.** The execution path from button click to API call is fully connected:

1. ✅ `ChatInput.handleSend()` calls `onSend(trimmed)` 
2. ✅ Parent (`ChatWindow`) passes `sendMessage` from `useChat()` as `onSend`
3. ✅ `useChat().sendChatMessage` calls `agent.service.sendMessage()`
4. ✅ `agent.service.sendMessage` calls `apiPost("/chat", request)`
5. ✅ `apiPost` hits `http://localhost:8000/api/v1/chat` via axios

The chain was correctly wired from the beginning. No fixes needed beyond adding debug logs.

---

## Files Modified (Debug Logs Added)

| File | Log Location | Console Output |
|------|-------------|----------------|
| `src/components/chat/ChatInput.tsx` | `handleSend()` | `[ChatInput] handleSend: <text>` |
| `src/components/chat/ChatWindow.tsx` | `handleSuggestion()` | `[ChatWindow] handleSuggestion: <text>` |
| `src/hooks/useChat.ts` | `sendChatMessage()` | `[useChat] sendChatMessage called: <text>` |
| `src/services/agent.service.ts` | `sendMessage()` | `[agent.service] sendMessage: <request>` |
| `src/lib/api.ts` | `apiPost()` | `[lib/api] POST: <url> <data>` |

---

## Expected Console Output When User Sends "baby formula"

```
[ChatInput] handleSend: baby formula
[useChat] sendChatMessage called: baby formula
[agent.service] sendMessage: {user_id: "550e8400-...", message: "baby formula", session_id: null}
[lib/api] POST: /chat {user_id: "550e8400-...", message: "baby formula", session_id: null}
```

---

## Before/After Flow

### Before (no issues found — was already correct)
```
ChatInput → onSend → useChat.sendChatMessage → agent.service.sendMessage → apiPost → backend
```

### After (with debug logs)
```
ChatInput → [LOG] → onSend → [LOG] → sendChatMessage → [LOG] → sendMessage → [LOG] → apiPost → backend
```

---

## Note on SituationInput.tsx

`SituationInput.tsx` (in `src/components/situation/`) is **only used on the home page** (`/`) in the legacy architecture. On `/chat`, the `ChatInput.tsx` component is used instead. Both are functional but serve different UX patterns:

| Component | Used On | Pattern |
|-----------|---------|---------|
| `SituationInput` | `/` (home, legacy) | Single textarea + "Generate Cart" button |
| `ChatInput` | `/chat` | Auto-resize + Enter to send + send icon button |
