# Hooks Report — NeedNow AI Frontend

## Summary

5 custom hooks implemented connecting services → stores with loading states, error handling, and reusable logic. Zero TypeScript errors.

---

## Hooks

| Hook | File | Service | Store | Features |
|------|------|---------|-------|----------|
| **useChat** | `useChat.ts` | `agent.service` | `chat.store` | Abort, optimistic messages, typing indicator |
| **useCart** | `useCart.ts` | `cart.service` | `cart.store` | Full CRUD, item count, loading/error |
| **useVoice** | `useVoice.ts` | `voice.service` | `chat.store` | Recording, transcription, voice chat, validation |
| **useMemory** | `useMemory.ts` | `memory.service` | `memory.store` | Granular updates, local+remote sync |
| **useEmergency** | `useEmergency.ts` | `agent.service` | `emergency.store` | Analyze, escalate, auto-activate, quick check |

---

## API

### `useChat()`
```typescript
const {
  messages,          // ChatMessage[]
  lastResult,        // { cart, urgency, reasoning, ecoAlternative, confidence }
  isTyping,          // boolean
  sessionId,         // string | null
  error,             // string | null
  sendMessage,       // (text: string) => Promise<ChatResponse | null>
  loadHistory,       // (sessionId: string) => Promise<data>
  cancel,            // () => void — aborts in-flight request
  clearChat,         // () => void
  newSession,        // () => void
} = useChat();
```

### `useCart()`
```typescript
const {
  items,             // CartItem[]
  totalAmount,       // number
  cartId,            // string | null
  itemCount,         // number (total quantity)
  loading,           // boolean
  error,             // string | null
  fetchCart,         // () => Promise<void>
  addItem,           // (productId, qty?) => Promise<boolean>
  removeItem,        // (productId) => Promise<boolean>
  emptyCart,         // () => Promise<boolean>
} = useCart();
```

### `useVoice()`
```typescript
const {
  recording,         // boolean
  loading,           // boolean
  error,             // string | null
  transcription,     // string | null
  startRecording,    // () => Promise<void>
  stopRecording,     // () => Promise<File | null>
  transcribe,        // (file) => Promise<TranscribeResponse | null>
  sendVoiceMessage,  // (file) => Promise<VoiceChatResponse | null>
  recordAndSend,     // () => Promise<VoiceChatResponse | null>
} = useVoice();
```

### `useMemory()`
```typescript
const {
  memory,                    // UserMemory
  isLoaded,                  // boolean
  lastUpdated,               // string | null
  fetchMemory,               // () => Promise<UserMemory | null>
  saveMemory,                // (updates) => Promise<boolean>
  addDietaryPreference,      // (pref) => Promise<void>
  removeDietaryPreference,   // (pref) => Promise<void>
  addPreferredBrand,         // (brand) => Promise<void>
  removePreferredBrand,      // (brand) => Promise<void>
  setBudgetLevel,            // (level) => Promise<void>
  setFamilySize,             // (size) => Promise<void>
  clearMemory,               // () => Promise<boolean>
} = useMemory();
```

### `useEmergency()`
```typescript
const {
  isActive,          // boolean
  analysis,          // { urgency, score, explanation, isEmergency, escalationRecommended }
  escalation,        // { escalated, workflowId, message, actions }
  isAnalyzing,       // boolean
  isEscalating,      // boolean
  error,             // string | null
  analyze,           // (text) => Promise<EmergencyAnalyzeResponse | null>
  escalate,          // (text, phone?) => Promise<EmergencyEscalateResponse | null>
  quickCheck,        // (text) => boolean — instant keyword detection
  activate,          // () => void
  deactivate,        // () => void
  reset,             // () => void
} = useEmergency();
```

---

## Architecture

```
Component
    │
    ├── useChat()     →  agent.service  →  chat.store
    ├── useCart()     →  cart.service   →  cart.store
    ├── useVoice()   →  voice.service  →  chat.store
    ├── useMemory()  →  memory.service →  memory.store
    └── useEmergency() → agent.service → emergency.store
                                              │
                                         user.store (userId)
```

---

## Key Patterns

| Pattern | Implementation |
|---------|---------------|
| **Loading states** | `useState(false)` with try/finally |
| **Error handling** | Catch → set error string → return null/false |
| **Abort/Cancel** | `AbortController` ref in useChat |
| **Optimistic updates** | User message added before API call (useChat) |
| **Local + Remote sync** | Store updated immediately, API called async (useMemory) |
| **Auto-activation** | Emergency mode activates when `is_emergency=true` (useEmergency) |
| **File validation** | `validateAudioFile()` before upload (useVoice) |

---

## TypeScript Verification

```
$ npx tsc --noEmit
Exit code: 0
```
