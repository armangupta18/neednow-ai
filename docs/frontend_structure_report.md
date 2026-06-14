# Frontend Structure Report — NeedNow AI

## Summary

- **Total files:** 91
- **Directories created:** 28
- **Files created/updated:** 47 new, 1 updated
- **Framework:** Next.js 15 (App Router)
- **State:** Zustand
- **API:** Axios with interceptors + AbortController
- **Styling:** Tailwind CSS 4 + shadcn/ui

---

## Directory Structure

```
src/
├── app/
│   ├── api/route.ts                    ← Health check API route
│   ├── cart/page.tsx, loading.tsx       ← Cart page
│   ├── chat/page.tsx, loading.tsx       ← Chat interface
│   ├── emergency/page.tsx              ← Emergency mode
│   ├── history/page.tsx                ← Chat history
│   ├── memory/page.tsx                 ← Preferences
│   ├── profile/page.tsx                ← User profile
│   ├── recommendations/page.tsx        ← Product recs
│   ├── sustainability/page.tsx         ← Eco dashboard
│   ├── layout.tsx                      ← Root layout
│   ├── page.tsx                        ← Home (situation input)
│   ├── error.tsx                       ← Error boundary
│   └── loading.css                     ← Loading styles
├── components/
│   ├── layout/Header.tsx, Footer.tsx
│   ├── recommendation/                 ← 6 result display components
│   ├── shared/LoadingSpinner, ErrorBoundary, EmptyState
│   ├── situation/SituationInput.tsx
│   └── ui/button.tsx                   ← shadcn
├── constants/
│   ├── api.ts                          ← Endpoints config
│   ├── routes.ts                       ← Route paths
│   └── urgency.ts                      ← Urgency level config
├── features/
│   ├── situation-to-cart/              ← Main shopping flow
│   ├── voice-commerce/                 ← Voice input
│   ├── emergency-mode/                 ← Emergency features
│   ├── memory-engine/                  ← Personalization
│   ├── recommendations/                ← Product recs
│   └── sustainability/                 ← Eco scoring
│       Each contains: components/ hooks/ services/ types.ts constants.ts
├── hooks/
│   ├── useChat.ts          ← POST /api/v1/chat (with abort, stores)
│   ├── useCart.ts          ← Cart CRUD operations
│   ├── useVoice.ts        ← Audio recording + transcription
│   ├── useMemory.ts       ← Memory store/retrieve
│   ├── useEmergency.ts    ← Emergency analyze/escalate
│   ├── useSustainability.ts ← Eco scores + alternatives
│   ├── useIntent.ts       ← Intent analysis (existing)
│   └── useSupervisor.ts   ← Legacy (to be replaced by useChat)
├── lib/
│   └── utils.ts            ← cn() utility
├── services/
│   ├── api.ts              ← Axios instance (timeout, interceptors)
│   ├── chatApi.ts          ← Chat API functions
│   ├── cartApi.ts          ← Cart API functions
│   ├── memoryApi.ts        ← Memory API functions
│   ├── voiceApi.ts         ← Voice API functions
│   ├── emergencyApi.ts     ← Emergency API functions
│   └── sustainabilityApi.ts ← Sustainability API functions
├── store/ (legacy)
│   └── useRecommendationStore.ts
├── stores/
│   ├── useChatStore.ts     ← Chat session + messages
│   ├── useCartStore.ts     ← Cart items + total
│   └── useUserStore.ts     ← User ID + name
├── styles/
│   └── globals.css
└── types/
    ├── api.ts              ← Generic API response types
    ├── cart.ts             ← Cart types (existing)
    ├── chat.ts             ← Chat types (matches backend exactly)
    ├── emergency.ts        ← Emergency request/response types
    ├── memory.ts           ← Memory/preference types
    ├── recommendation.ts   ← Legacy (needs update)
    ├── response.ts         ← Legacy intent response
    ├── sustainability.ts   ← Eco alternative types
    ├── urgency.ts          ← Urgency enum types
    └── voice.ts            ← Voice transcription types
```

---

## API Coverage

| Backend Endpoint | Service File | Hook | Status |
|-----------------|--------------|------|--------|
| POST /api/v1/chat | chatApi.ts | useChat.ts | ✅ Complete |
| POST /api/v1/cart/add | cartApi.ts | useCart.ts | ✅ Complete |
| POST /api/v1/cart/remove | cartApi.ts | useCart.ts | ✅ Complete |
| GET /api/v1/cart/{id} | cartApi.ts | useCart.ts | ✅ Complete |
| DELETE /api/v1/cart/{id} | cartApi.ts | useCart.ts | ✅ Complete |
| POST /api/v1/memory/store | memoryApi.ts | useMemory.ts | ✅ Complete |
| GET /api/v1/memory/{id} | memoryApi.ts | useMemory.ts | ✅ Complete |
| DELETE /api/v1/memory/{id} | memoryApi.ts | useMemory.ts | ✅ Complete |
| POST /api/v1/voice/transcribe | voiceApi.ts | useVoice.ts | ✅ Complete |
| POST /api/v1/voice/chat | voiceApi.ts | useVoice.ts | ✅ Complete |
| POST /api/v1/emergency/analyze | emergencyApi.ts | useEmergency.ts | ✅ Complete |
| POST /api/v1/emergency/escalate | emergencyApi.ts | useEmergency.ts | ✅ Complete |
| GET /api/v1/sustainability/score/{id} | sustainabilityApi.ts | useSustainability.ts | ✅ Complete |
| POST /api/v1/sustainability/recommend | sustainabilityApi.ts | useSustainability.ts | ✅ Complete |
| POST /api/v1/intent | api.ts | useIntent.ts | ✅ Existing |

---

## What Was Created vs. Existing

| Category | Existing | Created | Total |
|----------|----------|---------|-------|
| Pages | 4 | 6 | 10 |
| Components | 9 | 3 | 12 |
| Hooks | 2 | 6 | 8 |
| Services | 1 | 6 | 7 |
| Stores | 1 | 3 | 4 |
| Types | 5 | 5 | 10 |
| Constants | 0 | 3 | 3 |
| Features | 0 | 6×5=30 | 30 |

---

## Next Steps (Implementation Priority)

1. **Wire `useChat` into `page.tsx`** — replace `useSupervisor` usage
2. **Build ChatInterface component** — message list + input + voice
3. **Implement Cart page** — use `useCart` hook
4. **Fix legacy types** — update `recommendation.ts` and `response.ts`
5. **Delete `useSupervisor.ts`** — fully replaced by `useChat.ts`
6. **Build feature components** — fill feature folders with UI
