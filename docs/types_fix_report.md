# Frontend Types Fix Report — NeedNow AI

## Summary

The frontend TypeScript types have **significant mismatches** with the actual backend API responses. The primary issues:

1. `SupervisorResponse` in `recommendation.ts` uses `products[]` at top level — but the backend nests them inside `cart.products[]`.
2. Product fields use `name` — backend uses `title`.
3. `EcoAlternative` uses `name`/`eco_score`/`carbon_saved` — backend uses `alternative_product_name`/`sustainability_score`/`carbon_saved` (float).
4. The `useSupervisor` hook calls a non-existent `/api/v1/supervisor` endpoint.
5. Duplicate `EcoAlternative` interfaces in two files with conflicting shapes.

---

## Detailed Comparison

### Backend: Actual SupervisorResponse (from `/api/v1/chat`)

```json
{
  "session_id": "uuid",
  "user_message": { "user_id": "uuid", "content": "...", "role": "user", ... },
  "assistant_message": { "user_id": "uuid", "content": "...", "role": "assistant", ... },
  "cart": {
    "category": "baby",
    "products": [
      { "id": "uuid", "title": "Organic Baby Formula", "price": 24.99, "score": 95.5 }
    ],
    "bundles": [
      { "id": "uuid", "title": "Baby Wipes", "price": 5.99 }
    ]
  },
  "urgency": {
    "level": "HIGH",
    "score": 78,
    "explanation": "User described urgent need..."
  },
  "reasoning": "User needs baby formula urgently...",
  "eco_alternative": {
    "original_product_id": "uuid",
    "original_product_name": "Organic Baby Formula",
    "alternative_product_id": "uuid",
    "alternative_product_name": "Eco Formula Plus",
    "carbon_saved": 0.8,
    "price_difference": 2.0,
    "sustainability_score": 85.0
  },
  "metadata": { "memory_used": true, "confidence": 0.93 }
}
```

### Frontend: Current `SupervisorResponse` (WRONG)

```typescript
// src/types/recommendation.ts
interface SupervisorResponse {
  intent: string;           // ❌ Does not exist in backend
  urgency_level: string;    // ❌ Backend uses urgency.level
  reasoning: string;        // ✅ Correct
  products: Product[];      // ❌ Backend uses cart.products[]
  eco_alternative?: EcoAlternative;  // ⚠️ Wrong field names
}
```

---

## Field-by-Field Mismatches

### Products

| Frontend (`recommendation.ts`) | Backend (actual) | Fix |
|------|--------|-----|
| `product.name` | `product.title` | Rename to `title` |
| `product.quantity` | Not in supervisor response | Remove (only exists in cart API) |
| `product.image_url` | Not returned | Keep optional |
| `product.reason` | Not in supervisor response | Remove |
| — | `product.score` | Add `score: number` |

### EcoAlternative

| Frontend (`recommendation.ts`) | Backend (actual) | Fix |
|------|--------|-----|
| `name: string` | `alternative_product_name: string` | Rename |
| `eco_score: number` | `sustainability_score: number` | Rename |
| `carbon_saved: string` | `carbon_saved: number` | Change type to number |
| — | `original_product_id: string` | Add |
| — | `original_product_name: string` | Add |
| — | `alternative_product_id: string` | Add |
| — | `price_difference: number` | Add |

### Urgency

| Frontend (`urgency.ts`) | Backend (actual) | Status |
|------|--------|-----|
| `level: "CRITICAL" \| "HIGH" \| "MEDIUM" \| "LOW"` | `level: string` (same values) | ✅ Correct |
| `score: number` | `score: number` (0-100) | ✅ Correct |
| `explanation: string` | `explanation: string` | ✅ Correct |

### Cart (from cart API endpoints)

| Frontend (`cart.ts`) | Backend (`CartResponse`) | Status |
|------|--------|-----|
| `CartProduct.id` | `CartItemResponse.product_id` | ⚠️ Different field |
| `CartProduct.title` | `CartItemResponse.product_name` | ⚠️ Different field |
| `CartProduct.price` | `CartItemResponse.unit_price` | ⚠️ Different field |
| — | `CartItemResponse.id` (line item UUID) | Missing |
| — | `CartItemResponse.quantity` | Missing |
| — | `CartItemResponse.line_total` | Missing |

---

## Duplicate Interfaces

| Interface | File 1 | File 2 | Conflict |
|-----------|--------|--------|----------|
| `EcoAlternative` | `src/types/recommendation.ts` | `src/types/sustainability.ts` | Different field names and types |

---

## Fixed Types (Corrected Code)

### `src/types/recommendation.ts` — CORRECTED

```typescript
/** Product as returned in the supervisor cart.products[] array */
export interface CartProduct {
  id: string;
  title: string;
  price: number;
  score: number;
}

/** Bundle product suggestion */
export interface BundleProduct {
  id: string;
  title: string;
  price: number;
}

/** Supervisor cart output */
export interface SupervisorCart {
  category: string;
  products: CartProduct[];
  bundles: BundleProduct[];
}

/** Urgency assessment */
export interface Urgency {
  level: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  score: number;
  explanation: string;
}

/** Eco-friendly alternative from sustainability agent */
export interface EcoAlternative {
  original_product_id: string;
  original_product_name: string;
  alternative_product_id: string;
  alternative_product_name: string;
  carbon_saved: number;
  price_difference: number;
  sustainability_score: number;
}

/** Pipeline metadata */
export interface PipelineMetadata {
  memory_used: boolean;
  confidence: number;
  user_context?: string;
}

/** Full response from POST /api/v1/chat (via supervisor) */
export interface SupervisorResponse {
  session_id: string;
  user_message: AgentMessage;
  assistant_message: AgentMessage;
  cart: SupervisorCart;
  urgency: Urgency;
  reasoning: string;
  eco_alternative: EcoAlternative | null;
  recommended_products: Record<string, unknown>[];
  metadata: PipelineMetadata;
  timestamp: string;
}

/** Agent message shape */
export interface AgentMessage {
  user_id: string;
  session_id: string;
  content: string;
  role: "user" | "assistant" | "system";
  metadata: Record<string, unknown>;
  timestamp: string;
}
```

### `src/types/cart.ts` — CORRECTED (for cart API endpoints)

```typescript
/** Cart item from GET /api/v1/cart/{user_id} */
export interface CartItem {
  id: string;
  product_id: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  line_total: number;
}

/** Full cart response from cart API */
export interface CartResponse {
  user_id: string;
  cart_id: string;
  total_amount: number;
  items: CartItem[];
}

/** Response after add/remove */
export interface CartMutationResponse {
  message: string;
  cart: CartResponse;
}

/** Response after clearing cart */
export interface CartClearResponse {
  user_id: string;
  cleared: boolean;
  message: string;
}
```

### `src/types/sustainability.ts` — CORRECTED

```typescript
/** Eco alternative from sustainability analysis */
export interface EcoAlternative {
  original_product_id: string;
  original_product_name: string;
  alternative_product_id: string;
  alternative_product_name: string;
  carbon_saved: number;
  price_difference: number;
  sustainability_score: number;
}

/** Sustainability recommendation response */
export interface SustainabilityRecommendResponse {
  recommendations: EcoAlternative[];
  total_carbon_saved: number;
  overall_sustainability_score: number;
}

/** Product eco score */
export interface ProductEcoScore {
  product_id: string;
  product_name: string;
  category: string;
  sustainability_score: number;
}
```

### `src/types/urgency.ts` — NO CHANGES NEEDED ✅

### `src/types/response.ts` — CORRECTED

```typescript
/** Response from POST /api/v1/intent */
export interface IntentResponse {
  category: string;
  urgency: "low" | "medium" | "high" | "critical";
  budget: number | null;
  people_count: number | null;
  confidence: number;
}
```

---

## Removed Duplicates

| Remove | Keep | Reason |
|--------|------|--------|
| `EcoAlternative` in `recommendation.ts` (old version) | `EcoAlternative` in `sustainability.ts` | Sustainability file has correct fields; re-export from there |
| `Product` interface in `recommendation.ts` | `CartProduct` (renamed) | Matches actual backend field names |
| `IntentResponse` in `response.ts` (old cart-shaped version) | New `IntentResponse` | Old one mixed supervisor and intent responses |

---

## Component Impact (Changes Needed After Type Fixes)

| Component | Required Change |
|-----------|----------------|
| `ResultSection.tsx` | Access `result.urgency.level` instead of `result.urgency_level` |
| `CartView.tsx` | Access `product.title` instead of `product.name`; remove `product.quantity` |
| `CartItem.tsx` | Use `product.title` instead of `product.name` |
| `EcoAlternativeCard.tsx` | Use `alternative.alternative_product_name`, `alternative.sustainability_score`, `alternative.carbon_saved` |
| `page.tsx` | Response is now `SupervisorResponse` with nested `cart` |

---

## Recommended Fix Order

1. Fix `src/types/sustainability.ts` (canonical `EcoAlternative`)
2. Fix `src/types/recommendation.ts` (remove old interfaces, add correct ones)
3. Fix `src/types/cart.ts` (match cart API endpoints)
4. Fix `src/types/response.ts` (correct `IntentResponse`)
5. Delete duplicate `EcoAlternative` from `recommendation.ts` (import from sustainability)
6. Update components to use new field names
