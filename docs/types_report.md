# Types Report — NeedNow AI Frontend

## Summary

5 type modules implemented with complete interfaces matching all backend API schemas. Strict typing enforced, backward compatibility preserved for existing components.

**TypeScript: ✅ Zero errors**

---

## Files

| File | Interfaces | Purpose |
|------|-----------|---------|
| `types/agent.ts` | 17 | Agent pipeline types: message, intent, urgency, sustainability, supervisor, chat, emergency |
| `types/product.ts` | 8 + 2 functions | Product model, search, eco scores, stock helpers |
| `types/cart.ts` | 7 + 4 functions | Cart CRUD: items, responses, mutations, utility functions |
| `types/memory.ts` | 8 + constants | User memory: short-term, long-term, preferences, budget levels |
| `types/recommendation.ts` | 9 + 1 function | Recommendations: items, history, sustainability, pipeline result converter |
| `types/index.ts` | — | Barrel re-export |

---

## Key Interfaces

### Agent Pipeline (`agent.ts`)
```typescript
AgentMessage          // Chat messages (user/assistant/system)
IntentResponse        // Intent detection result
UrgencyResponse       // Urgency scoring
Urgency               // Urgency in supervisor context
EcoAlternative        // Sustainability alternative
SupervisorCart        // Cart with products + bundles
SupervisorResponse    // Full pipeline response
ChatResponse          // API response from POST /chat
ChatRequest           // API request to POST /chat
EmergencyAnalyzeResponse  // Emergency urgency analysis
EmergencyEscalateResponse // Emergency workflow result
```

### Product (`product.ts`)
```typescript
Product               // Full product from DB
RecommendedProduct    // Product in recommendation context (id, title, price, score)
BundleProduct         // Bundle suggestion
ProductSearchResult   // Vector search result with similarity
ProductEcoScore       // Individual product sustainability score
SustainabilityScoreBreakdown  // 5-dimension breakdown
getStockStatus()      // Stock → "in_stock" | "low_stock" | "out_of_stock"
```

### Cart (`cart.ts`)
```typescript
CartItem              // Line item (product_id, quantity, unit_price, line_total)
CartResponse          // Full cart (items + total)
CartAddRequest        // Add to cart payload
CartRemoveRequest     // Remove from cart payload
CartMutationResponse  // Response after add/remove
CartClearResponse     // Response after clear
calculateCartTotal()  // Client-side total
isInCart()           // Check if product exists in cart
```

### Memory (`memory.ts`)
```typescript
UserMemory            // Core preferences
BudgetLevel           // "low" | "medium" | "high" | "premium"
StoreMemoryRequest    // Save memory payload
MemoryResponse        // API response
ShortTermMemory       // Session context (decays)
LongTermMemory        // Persistent profile
MemoryState           // Combined state
DEFAULT_MEMORY        // Empty memory constant
BUDGET_LABELS         // Display-friendly labels
```

### Recommendation (`recommendation.ts`)
```typescript
RecommendationRequest // Generate recommendations
RecommendationItem    // Single recommended product with scores
RecommendationResponse // Full recommendation set
RecommendationRecord  // Stored recommendation history
PipelineResult        // UI-friendly view of ChatResponse
toPipelineResult()    // ChatResponse → PipelineResult converter
```

---

## Backward Compatibility

Legacy interfaces preserved for existing components:
- `Product` (with `name` field — deprecated, use `RecommendedProduct`)
- `SupervisorResponse` (old flat shape — deprecated, use `ChatResponse`)
- `EcoAlternative` (old shape with `name`/`eco_score` — deprecated, use agent version)

These will be removed once components are updated.

---

## Utility Functions Included

| Function | File | Returns |
|----------|------|---------|
| `getStockStatus(stock)` | product.ts | `"in_stock" \| "low_stock" \| "out_of_stock"` |
| `getStockLabel(status)` | product.ts | Human-readable label |
| `calculateCartTotal(items)` | cart.ts | Total price |
| `calculateCartItemCount(items)` | cart.ts | Total quantity |
| `isInCart(items, productId)` | cart.ts | Boolean |
| `getCartItem(items, productId)` | cart.ts | CartItem or undefined |
| `toPipelineResult(chat)` | recommendation.ts | UI-friendly PipelineResult |
