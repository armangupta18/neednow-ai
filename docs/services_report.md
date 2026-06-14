# API Services Report — NeedNow AI Frontend

## Summary

5 service modules connecting to all backend API endpoints. Fully typed, using centralized `apiGet`/`apiPost`/`apiDelete` helpers. Zero TypeScript errors.

---

## Services

| Service | File | Backend Endpoints | Functions |
|---------|------|-------------------|-----------|
| **Agent** | `agent.service.ts` | `/chat`, `/intent`, `/emergency/*` | 6 |
| **Cart** | `cart.service.ts` | `/cart/add`, `/cart/remove`, `/cart/{id}` | 5 |
| **Voice** | `voice.service.ts` | `/voice/transcribe`, `/voice/chat` | 2 + validators |
| **Memory** | `memory.service.ts` | `/memory/store`, `/memory/{id}` | 7 |
| **Sustainability** | `sustainability.service.ts` | `/sustainability/score/{id}`, `/recommend`, `/analyze` | 4 + batch + helpers |

---

## Function Reference

### `agent.service.ts`
| Function | Endpoint | Returns |
|----------|----------|---------|
| `sendMessage(request, signal?)` | POST `/chat` | `ChatResponse` |
| `getChatHistory(sessionId, userId)` | GET `/chat/{id}/history` | Messages |
| `analyzeIntent(text, userId)` | POST `/intent` | `IntentResponse` |
| `analyzeEmergency(request)` | POST `/emergency/analyze` | `EmergencyAnalyzeResponse` |
| `escalateEmergency(request)` | POST `/emergency/escalate` | `EmergencyEscalateResponse` |
| `checkEmergencyHealth()` | GET `/emergency/health` | Status |

### `cart.service.ts`
| Function | Endpoint | Returns |
|----------|----------|---------|
| `getCart(userId)` | GET `/cart/{id}` | `CartResponse` |
| `addToCart(userId, productId, qty)` | POST `/cart/add` | `CartMutationResponse` |
| `removeFromCart(userId, productId, qty?)` | POST `/cart/remove` | `CartMutationResponse` |
| `clearCart(userId)` | DELETE `/cart/{id}` | `CartClearResponse` |
| `addMultipleToCart(userId, items[])` | Sequential POST | `CartMutationResponse[]` |

### `voice.service.ts`
| Function | Endpoint | Returns |
|----------|----------|---------|
| `transcribeAudio(file, userId, lang)` | POST `/voice/transcribe` | `TranscribeResponse` |
| `voiceChat(file, userId, options?)` | POST `/voice/chat` | `VoiceChatResponse` |
| `validateAudioFile(file)` | — | Error string or null |

### `memory.service.ts`
| Function | Endpoint | Returns |
|----------|----------|---------|
| `getMemory(userId)` | GET `/memory/{id}` | `MemoryResponse` |
| `storeMemory(userId, memory)` | POST `/memory/store` | `MemoryResponse` |
| `clearMemory(userId)` | DELETE `/memory/{id}` | `ClearMemoryResponse` |
| `updatePreference(userId, key, val)` | POST `/memory/store` | `MemoryResponse` |
| `addDietaryPreference(userId, pref)` | GET + POST | `MemoryResponse` |
| `addPreferredBrand(userId, brand)` | GET + POST | `MemoryResponse` |
| `setBudgetLevel(userId, level)` | POST `/memory/store` | `MemoryResponse` |

### `sustainability.service.ts`
| Function | Endpoint | Returns |
|----------|----------|---------|
| `getProductEcoScore(productId)` | GET `/sustainability/score/{id}` | `ProductEcoScore` |
| `getEcoRecommendations(productIds)` | POST `/sustainability/recommend` | `SustainabilityRecommendResponse` |
| `generateSustainabilityReport(ids)` | POST `/sustainability/analyze` | `SustainabilityReportResponse` |
| `batchGetEcoScores(productIds)` | Parallel GET | `Map<string, ProductEcoScore>` |
| `getSustainabilityLabel(score)` | — | "Excellent"/"Good"/etc. |
| `getSustainabilityColor(score)` | — | Tailwind class |
| `formatCarbonSaved(kg)` | — | "1.2 kg CO₂ saved" |

---

## Architecture

```
Component → Hook → Service → lib/api.ts → Backend
     ↕               ↕
   Store         constants/routes.ts (endpoint paths)
```

All services use:
- `apiGet<T>` / `apiPost<T>` / `apiDelete<T>` from `@/lib/api`
- `API_ROUTES` from `@/constants/routes` for endpoint paths
- Types from `@/types/*` for request/response typing

---

## TypeScript Verification

```
$ npx tsc --noEmit
Exit code: 0
```
