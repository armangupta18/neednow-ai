# Constants Report — NeedNow AI Frontend

## Summary

4 constants modules + barrel export created with production-ready configuration values. Zero TypeScript errors.

---

## Files

| File | Constants | Purpose |
|------|-----------|---------|
| `constants/routes.ts` | 13 routes + 5 nav items + full API route map | Application navigation & API paths |
| `constants/prompts.ts` | 20+ messages | UI copy: placeholders, welcome, errors, empty states, success |
| `constants/agent-config.ts` | 7 agents + pipeline config + model info | Agent metadata, categories, confidence thresholds |
| `constants/emergency.ts` | 4 urgency levels + 5 actions + keywords | Emergency mode: levels, colors, delivery times, detection |
| `constants/index.ts` | — | Barrel re-export |

---

## Key Exports

### `routes.ts`
- `ROUTES` — Page paths (`/`, `/chat`, `/cart`, `/emergency`, etc.)
- `NAV_ITEMS` — Header navigation with icons
- `API_ROUTES` — All backend endpoint paths (typed, with dynamic params)

### `prompts.ts`
- `CHAT_PLACEHOLDERS` — Rotating chat input placeholders
- `CHAT_WELCOME_MESSAGE` — First-time greeting
- `SITUATION_EXAMPLES` — 6 example situations for guidance
- `VOICE_*` — Voice recording prompts
- `EMPTY_STATES` — Empty state copy for cart, history, recommendations, memory, search
- `SUCCESS_MESSAGES` — Toast/notification messages

### `agent-config.ts`
- `AGENTS` — Agent ID enum
- `AGENT_INFO` — Display metadata (name, description, icon, color) per agent
- `PIPELINE_STEPS` — Ordered pipeline display
- `MODEL_CONFIG` — LLM, embedding, and vector store specs
- `CONFIDENCE` — Score thresholds (high ≥ 0.8, medium ≥ 0.5, low ≥ 0.3)
- `PRODUCT_CATEGORIES` — 14 supported categories
- `getConfidenceLabel()` / `getConfidenceColor()` — Display helpers

### `emergency.ts`
- `URGENCY_CONFIG` — Full urgency level config (label, color, bgColor, icon, deliveryLabel, estimatedTime)
- `EMERGENCY_ACTIONS` — 5 escalation actions with metadata
- `EMERGENCY_KEYWORDS` — 16 trigger keywords for detection
- `EMERGENCY_CONTACTS` — Indian emergency numbers
- `URGENCY_THRESHOLDS` — Score cutoffs (90/70/40/0)
- `getUrgencyFromScore()` / `isEmergencyScore()` / `containsEmergencyKeyword()` — Utility functions

---

## Usage Examples

```typescript
import {
  ROUTES,
  NAV_ITEMS,
  API_ROUTES,
  URGENCY_CONFIG,
  AGENT_INFO,
  SITUATION_EXAMPLES,
  getUrgencyFromScore,
  getConfidenceLabel,
} from "@/constants";

// Get urgency display config
const level = getUrgencyFromScore(85); // "HIGH"
const config = URGENCY_CONFIG[level];
// → { label: "High Priority", color: "text-orange-700", estimatedTime: "1-2 hours", ... }

// Show agent info
const intent = AGENT_INFO.intent;
// → { name: "Intent Agent", icon: "🧠", color: "text-blue-600", ... }

// Navigate
<Link href={ROUTES.EMERGENCY}>Emergency</Link>

// API call
await api.post(API_ROUTES.CART.ADD, { user_id, product_id, quantity });
```

---

## TypeScript Verification

```
$ npx tsc --noEmit
Exit code: 0
```
