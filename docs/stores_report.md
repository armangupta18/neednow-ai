# Zustand Stores Report — NeedNow AI Frontend

## Summary

5 Zustand stores implemented with persistence, type safety, actions, and selectors. Zero TypeScript errors.

---

## Stores

| Store | File | Persisted | Keys |
|-------|------|-----------|------|
| **Cart** | `cart.store.ts` | ✅ localStorage | cartId, items, totalAmount |
| **Chat** | `chat.store.ts` | ✅ localStorage (last 50 msgs) | sessionId, messages, lastResult, isTyping |
| **User** | `user.store.ts` | ✅ localStorage | userId, profile, token, isAuthenticated |
| **Memory** | `memory.store.ts` | ✅ localStorage | memory (preferences), lastUpdated |
| **Emergency** | `emergency.store.ts` | ❌ session-only | isActive, analysis, escalation |

---

## Actions & Selectors

### Cart Store
**Actions:**
- `setCart(cartId, userId, items, total)` — Set full cart from API
- `addItem(item)` — Add or increment item
- `removeItem(productId)` — Remove by product ID
- `updateQuantity(productId, quantity)` — Update quantity + recalculate
- `clearCart()` — Empty cart

**Selectors:**
- `selectCartItems` / `selectCartTotal` / `selectCartItemCount`
- `selectIsInCart(productId)` / `selectCartItem(productId)`

---

### Chat Store
**Actions:**
- `setSessionId(id)` — Set active session
- `addMessage(msg)` — Append message
- `setMessages(msgs)` — Replace all messages
- `setLastResult(result)` — Store pipeline result
- `setIsTyping(bool)` — Toggle typing indicator
- `clearChat()` / `newSession()` — Reset state

**Selectors:**
- `selectMessages` / `selectSessionId` / `selectLastResult`
- `selectIsTyping` / `selectMessageCount` / `selectLastMessage`
- `selectHasSession`

**Persistence:** Only last 50 messages via `partialize`

---

### User Store
**Actions:**
- `setUser(profile, token?)` — Login / set user
- `setToken(token)` — Update JWT
- `updateProfile(updates)` — Partial profile update
- `logout()` — Clear all auth state

**Selectors:**
- `selectUserId` / `selectProfile` / `selectIsAuthenticated`
- `selectUserName` / `selectToken`

**Default:** Demo user UUID for hackathon (`550e8400-...`)

---

### Memory Store
**Actions:**
- `setMemory(memory)` — Set from API response
- `updatePreferences(updates)` — Partial update
- `addDietaryPreference(pref)` / `removeDietaryPreference(pref)`
- `addPreferredBrand(brand)` / `removePreferredBrand(brand)`
- `setBudgetLevel(level)` / `setFamilySize(size)`
- `setSustainabilityScore(score)`
- `resetMemory()` / `markLoaded()`

**Selectors:**
- `selectMemory` / `selectIsMemoryLoaded` / `selectLastUpdated`
- `selectDietaryPreferences` / `selectPreferredBrands`
- `selectBudgetLevel` / `selectFamilySize` / `selectSustainabilityScore`

---

### Emergency Store
**Actions:**
- `activateEmergency()` / `deactivateEmergency()`
- `setAnalysis(analysis)` / `setEscalation(escalation)`
- `setAnalyzing(bool)` / `setEscalating(bool)`
- `setError(msg)` / `reset()`

**Selectors:**
- `selectIsEmergencyActive` / `selectEmergencyAnalysis`
- `selectEscalation` / `selectIsAnalyzing` / `selectIsEscalating`
- `selectEmergencyError` / `selectIsEmergencyLevel` / `selectUrgencyLevel`

**No persistence:** Emergency state is intentionally session-only.

---

## Usage

```typescript
import { useCartStore, selectCartTotal, selectIsInCart } from "@/stores";

// In component
const total = useCartStore(selectCartTotal);
const isInCart = useCartStore(selectIsInCart("product-uuid"));
const addItem = useCartStore((s) => s.addItem);

// In hook
const { addItem, clearCart } = useCartStore();
```

---

## Persistence Strategy

| Store | Storage Key | Partialize |
|-------|-------------|-----------|
| Cart | `neednow-cart` | Full state |
| Chat | `neednow-chat` | sessionId + last 50 messages + lastResult |
| User | `neednow-user` | Full state |
| Memory | `neednow-memory` | Full state |
| Emergency | — | Not persisted |

All use `createJSONStorage(() => localStorage)` with SSR-safe fallback.

---

## TypeScript Verification

```
$ npx tsc --noEmit
Exit code: 0
```
