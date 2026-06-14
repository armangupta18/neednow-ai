# Frontend Audit — NeedNow AI

## 1. Existing Files

### Pages (Next.js App Router)
| File | Status | Notes |
|------|--------|-------|
| `src/app/page.tsx` | ✅ Exists | Main chat/situation input page |
| `src/app/layout.tsx` | ✅ Exists | Root layout with Header/Footer |
| `src/app/cart/page.tsx` | ⚠️ Stub | Empty placeholder (no functionality) |
| `src/app/history/page.tsx` | ⚠️ Stub | Empty placeholder (no functionality) |
| `src/app/globals.css` | ❓ Referenced | Imported in layout but not verified |

### Components
| File | Status | Notes |
|------|--------|-------|
| `src/components/layout/Header.tsx` | ✅ Complete | Nav links to Home/Cart/History |
| `src/components/layout/Footer.tsx` | ✅ Complete | "Powered by Amazon Bedrock" |
| `src/components/situation/SituationInput.tsx` | ✅ Complete | Textarea + submit button |
| `src/components/recommendation/ResultSection.tsx` | ✅ Complete | Orchestrates result display |
| `src/components/recommendation/CartView.tsx` | ✅ Complete | Product list + total |
| `src/components/recommendation/CartItem.tsx` | ✅ Complete | Single product card |
| `src/components/recommendation/UrgencyBadge.tsx` | ✅ Complete | Color-coded urgency pill |
| `src/components/recommendation/ReasoningPanel.tsx` | ✅ Complete | AI reasoning display |
| `src/components/recommendation/EcoAlternativeCard.tsx` | ✅ Complete | Green eco card |
| `src/components/ui/button.tsx` | ✅ Exists | shadcn/ui button |

### Hooks
| File | Status | Notes |
|------|--------|-------|
| `src/hooks/useSupervisor.ts` | ⚠️ Issues | Calls non-existent `/api/v1/supervisor` endpoint |
| `src/hooks/useIntent.ts` | ✅ Works | Calls `/api/v1/intent` correctly |

### Services
| File | Status | Notes |
|------|--------|-------|
| `src/services/api.ts` | ✅ Complete | Axios instance with baseURL |

### Store
| File | Status | Notes |
|------|--------|-------|
| `src/store/useRecommendationStore.ts` | ✅ Complete | Zustand store for results |

### Types
| File | Status | Notes |
|------|--------|-------|
| `src/types/recommendation.ts` | ⚠️ Mismatch | Does not match backend `SupervisorResponse` schema |
| `src/types/response.ts` | ✅ Matches | Matches backend intent/supervisor response shape |
| `src/types/cart.ts` | ✅ Matches | Matches backend cart structure |
| `src/types/urgency.ts` | ✅ Matches | Matches backend urgency schema |
| `src/types/sustainability.ts` | ✅ Matches | Matches backend eco alternative |

### Config
| File | Status |
|------|--------|
| `package.json` | ✅ Valid |
| `tsconfig.json` | ✅ Exists |
| `next.config.ts` | ✅ Exists |
| `components.json` | ✅ shadcn config |
| `lib/utils.ts` | ✅ cn() utility |

---

## 2. Missing Files

| Expected File | Purpose | Priority |
|---------------|---------|----------|
| `src/app/globals.css` | Tailwind directives | HIGH (may exist, not listed) |
| `src/hooks/useChat.ts` | Chat API integration (POST /chat) | HIGH |
| `src/hooks/useCart.ts` | Cart API integration (add/remove/get/clear) | HIGH |
| `src/hooks/useVoice.ts` | Voice input via microphone | MEDIUM |
| `src/services/chatApi.ts` | Typed chat API calls | HIGH |
| `src/services/cartApi.ts` | Typed cart API calls | HIGH |
| `src/services/memoryApi.ts` | Memory store/retrieve API | MEDIUM |
| `src/services/sustainabilityApi.ts` | Sustainability scores API | LOW |
| `src/store/useCartStore.ts` | Cart state management | HIGH |
| `src/store/useChatStore.ts` | Chat history state | HIGH |
| `src/components/chat/ChatInterface.tsx` | Conversational chat UI | HIGH |
| `src/components/chat/MessageBubble.tsx` | Chat message rendering | HIGH |
| `src/components/chat/VoiceButton.tsx` | Voice input button | MEDIUM |
| `src/components/cart/CartPage.tsx` | Full cart page content | HIGH |
| `src/components/history/HistoryPage.tsx` | Chat history display | MEDIUM |
| `src/components/sustainability/ScoreCard.tsx` | Product eco score | LOW |
| `src/types/chat.ts` | Chat message types | HIGH |
| `src/types/memory.ts` | Memory/preference types | MEDIUM |
| `.env.local` | `NEXT_PUBLIC_API_URL` | HIGH |

---

## 3. Broken Imports

| File | Import | Issue |
|------|--------|-------|
| `src/hooks/useSupervisor.ts` | Direct `fetch` to `/api/v1/supervisor` | Endpoint does not exist — backend uses `/api/v1/chat` |
| `src/app/page.tsx` | Uses `useSupervisor` | Should use `useChat` or updated hook |
| `src/components/recommendation/ResultSection.tsx` | `SupervisorResponse` from `@/types/recommendation` | Type shape doesn't match actual backend response |

---

## 4. TypeScript Issues

| File | Issue |
|------|-------|
| `src/types/recommendation.ts` | `SupervisorResponse` has `products: Product[]` but backend returns `cart.products` with different field names (`title` vs `name`) |
| `src/hooks/useSupervisor.ts` | No error handling, no TypeScript return type, uses string `"demo-user"` as user_id (should be UUID) |
| `src/hooks/useIntent.ts` | Hardcoded UUID for `user_id` — should come from auth/store |
| `src/components/recommendation/CartView.tsx` | Accesses `product.quantity` but type `Product` may not have it from backend |
| `src/components/recommendation/EcoAlternativeCard.tsx` | Uses `alternative.name` and `alternative.eco_score` but backend returns `alternative_product_name` and `sustainability_score` |

---

## 5. Incomplete Components

| Component | What's Missing |
|-----------|---------------|
| `CartPage` (`src/app/cart/page.tsx`) | No cart API integration, no product listing, no add/remove actions |
| `HistoryPage` (`src/app/history/page.tsx`) | No chat history API call, no conversation rendering |
| `Header` | No active link highlighting, no user auth indicator |
| `SituationInput` | No loading state indicator, no voice input, no error display |
| `ResultSection` | No "Add to Cart" button on products, no loading skeleton |

---

## 6. Missing API Integrations

| Backend Endpoint | Frontend Integration | Status |
|------------------|---------------------|--------|
| `POST /api/v1/chat` | `useChat` hook + ChatInterface | ❌ Missing |
| `POST /api/v1/cart/add` | Cart add button + store | ❌ Missing |
| `POST /api/v1/cart/remove` | Cart remove action | ❌ Missing |
| `GET /api/v1/cart/{user_id}` | Cart page data fetch | ❌ Missing |
| `DELETE /api/v1/cart/{user_id}` | Clear cart button | ❌ Missing |
| `POST /api/v1/memory/store` | Save user preferences | ❌ Missing |
| `GET /api/v1/memory/{user_id}` | Load user preferences | ❌ Missing |
| `POST /api/v1/voice/transcribe` | Voice input component | ❌ Missing |
| `POST /api/v1/voice/chat` | Voice-to-chat pipeline | ❌ Missing |
| `POST /api/v1/emergency/analyze` | Urgency alert display | ❌ Missing |
| `GET /api/v1/sustainability/score/{id}` | Product eco badge | ❌ Missing |
| `POST /api/v1/intent` | Intent analysis | ✅ Exists (useIntent hook) |

---

## 7. Missing Pages

| Route | Purpose | Priority |
|-------|---------|----------|
| `/chat` | Dedicated conversational chat interface | HIGH |
| `/sustainability` | Product sustainability dashboard | MEDIUM |
| `/profile` | User preferences & memory management | MEDIUM |
| `/emergency` | Emergency mode with priority actions | LOW (merge into chat) |

---

## 8. Recommended Implementation Order

### Phase 1 — Core Chat (Highest Priority)
1. Create `.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000`
2. Fix `src/types/recommendation.ts` to match actual `SupervisorResponse` from backend
3. Create `src/hooks/useChat.ts` — calls `POST /api/v1/chat`
4. Create `src/types/chat.ts` — chat message types
5. Create `src/store/useChatStore.ts` — conversation state
6. Create `src/components/chat/ChatInterface.tsx` — message list + input
7. Create `src/components/chat/MessageBubble.tsx` — individual messages
8. Update `src/app/page.tsx` to use chat interface (replace situation input pattern)

### Phase 2 — Cart Integration
9. Create `src/hooks/useCart.ts` — add/remove/get/clear
10. Create `src/store/useCartStore.ts` — cart state
11. Implement `src/app/cart/page.tsx` — full cart with products
12. Add "Add to Cart" buttons in recommendation results
13. Fix `EcoAlternativeCard.tsx` to use correct field names

### Phase 3 — Voice & UX
14. Create `src/hooks/useVoice.ts` — audio recording + transcription
15. Create `src/components/chat/VoiceButton.tsx` — microphone input
16. Add loading states/skeletons to all components
17. Add error handling/toast notifications

### Phase 4 — Memory & Personalization
18. Create `src/services/memoryApi.ts` — store/retrieve preferences
19. Create `/profile` page — preference management
20. Display personalization indicator in results

### Phase 5 — Sustainability & Polish
21. Create sustainability score badges on products
22. Implement `/sustainability` dashboard page
23. Implement `/history` page with conversation replay
24. Add responsive design breakpoints
25. Add dark mode support
