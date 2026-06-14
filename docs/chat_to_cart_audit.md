# Chat-to-Cart Audit — NeedNow AI

## Root Cause

**Two issues prevented product generation:**

1. **`RetrievalService` returned empty results** when FAISS index was unavailable — it had no fallback to query products from PostgreSQL.

2. **`SustainabilityAgent` crashed** because it accessed `product.id` on `ProductCandidate` objects (which use `product_id`), causing the entire pipeline to return 500.

## Request Path (Fixed)

```
POST /api/v1/chat { message, user_id }
  └── ChatService.process_message()
        └── SupervisorAgent.execute()
              ├── Step 1: IntentAgent.analyze() → category, urgency, budget
              ├── Step 1: UrgencyAgent.analyze() → urgency level, score
              ├── Step 2: ProductAgent.recommend()
              │     ├── EmbeddingService.generate_embedding() → mock vector
              │     ├── RetrievalService.retrieve(embedding, category)
              │     │     └── [FIXED] _fallback_retrieve() → SELECT FROM products WHERE category ILIKE
              │     ├── RankingService.rank() → sorted by score
              │     └── BundleService.generate() → bundle suggestions
              ├── Step 3: SustainabilityAgent.analyze(top_products)
              │     └── [FIXED] Uses getattr() for product_id/id compatibility
              ├── Step 4: Build cart dict with products + bundles
              └── Step 5: Build reasoning text
                    └── Return SupervisorResponse
```

## Files Modified

| File | Change |
|------|--------|
| `app/agents/product/retrieval_service.py` | Added `_fallback_retrieve()` — queries PostgreSQL by category when FAISS is unavailable |
| `app/agents/product/agent.py` | Pass `category` to `retrieve()`, fixed confidence calculation for empty results |
| `app/agents/sustainability/agent.py` | Used `getattr()` for `id`/`product_id` compatibility, wrapped `find_alternatives` in try/except |

## Before vs After

| Metric | Before | After |
|--------|--------|-------|
| Products in response | 0 | **10** |
| Status code | 500 (sustainability crash) | **200** |
| Cart category | None | **personal_care** |
| Confidence | None | **0.92** |
| Eco alternative | None | **Present** |
| Urgency | None | **MEDIUM** |
| Bundles | 0 | 0 (correct — no keyword matches) |

## Example Successful Response

```json
{
  "session_id": "...",
  "cart": {
    "category": "personal_care",
    "products": [
      { "id": "...", "title": "Blood Pressure Monitor", "price": 22.25, "score": 92.0 },
      { "id": "...", "title": "Digital Thermometer", "price": 15.99, "score": 89.0 }
    ],
    "bundles": []
  },
  "urgency": { "level": "MEDIUM", "score": 69, "explanation": "..." },
  "reasoning": "Detected category 'personal_care'. Urgency...",
  "eco_alternative": { "alternative_product_name": "Eco Product...", "carbon_saved": 0.5 },
  "metadata": { "memory_used": true, "confidence": 0.92 }
}
```

## Verification

- ✅ 324 tests pass
- ✅ `POST /api/v1/chat` returns 200 with products
- ✅ Products retrieved from PostgreSQL (60,288 in DB)
- ✅ Sustainability analysis runs without crash
- ✅ Frontend receives product data for cart display
