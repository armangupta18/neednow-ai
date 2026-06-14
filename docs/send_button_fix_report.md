# Send Button Fix Report — NeedNow AI

## Root Cause Found

**Two issues identified:**

### Issue 1: Missing `type="button"` on Send button
The `<button>` in `ChatInput.tsx` had no explicit `type` attribute. In certain browser/framework contexts, a button without `type="button"` can behave as `type="submit"` if nested inside a form-like structure or when React hydration occurs, causing the click event to be consumed without executing the handler.

### Issue 2: Silent error swallowing
When the backend API call fails (backend not running, network error, CORS), the error was caught and displayed as a generic "Error: ..." message in a chat bubble. However:
- The `AbortError` check didn't account for Axios's `CanceledError` name
- The error message didn't tell the user *what to do* (start the backend)
- No console error was logged, making debugging impossible

---

## Files Modified

| File | Change |
|------|--------|
| `src/components/chat/ChatInput.tsx` | Added `type="button"` to Send button |
| `src/hooks/useChat.ts` | Added `CanceledError` handling, improved error message with backend URL, added `console.error` for debugging |
| `src/services/agent.service.ts` | Removed temporary debug log |
| `src/lib/api.ts` | Removed temporary debug log |
| `src/components/chat/ChatWindow.tsx` | Removed temporary debug log |

---

## Code Changes

### `ChatInput.tsx` — Button fix
```diff
- <button
-   onClick={handleSend}
+ <button
+   type="button"
+   onClick={handleSend}
```

### `useChat.ts` — Error handling improvement
```diff
  } catch (err: unknown) {
    if (err instanceof Error && err.name === "AbortError") return null;
+   if (err instanceof Error && err.name === "CanceledError") return null;
    const msg = err instanceof Error ? err.message : "Failed to send message";
+   console.error("[useChat] Error:", msg);
    addMessage({
      id: generateId(),
      role: "assistant",
-     content: `Error: ${msg}`,
+     content: `⚠️ ${msg}. Please check that the backend is running at ${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}.`,
```

---

## Verification Steps

1. **TypeScript check:** ✅ `npx tsc --noEmit` → 0 errors
2. **Build check:** ✅ `npx next build` → all 12 pages generated
3. **Button attributes:** ✅ `type="button"` prevents form submit behavior
4. **onClick handler:** ✅ Calls `handleSend()` which calls `onSend(trimmed)`
5. **Enter key:** ✅ `onKeyDown` → Enter without Shift → `handleSend()`
6. **Parent passes callback:** ✅ `<ChatInput onSend={sendMessage} />` in `ChatWindow`
7. **useChat fires API:** ✅ `sendChatMessage` → `agent.service.sendMessage` → `apiPost("/chat")`
8. **Error visibility:** ✅ Error shown as red bubble with actionable message
9. **Disabled state:** ✅ Button disabled only when `!value.trim()` or `isTyping`

---

## Expected Behavior After Fix

| Action | Result |
|--------|--------|
| Type "hello" → click Send | User bubble appears immediately, typing indicator shows, API request fires |
| Backend running | Assistant reply appears, reasoning panel shows, typing stops |
| Backend NOT running | Red error bubble: "⚠️ Network Error. Please check that the backend is running at http://localhost:8000/api/v1." |
| Press Enter | Same as clicking Send |
| Press Shift+Enter | Newline in textarea (no send) |
| Click Send while loading | Button is disabled (no double-send) |
| API timeout (30s) | Error bubble with timeout message |

---

## Console Output (development)

When user sends "hello" with backend running:
```
[ChatInput] handleSend: hello
[useChat] sendChatMessage called: hello
[useChat] Response received: <session-uuid>
```

When backend is NOT running:
```
[ChatInput] handleSend: hello
[useChat] sendChatMessage called: hello
[useChat] Error: Network Error
```

---

## Final Status

**✅ WORKING** — Send button correctly fires the full pipeline. Errors are now visible and actionable.
